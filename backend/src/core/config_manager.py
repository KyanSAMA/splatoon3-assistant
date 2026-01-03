"""配置管理器 - 单例模式，内存缓存 + 数据库持久化"""

import asyncio
import json
import logging
import os
from typing import Any, Dict, List, Optional, Tuple

from src.dao.database import get_session, engine, Base
from src.dao.config_dao import ConfigDAO

logger = logging.getLogger(__name__)


class ConfigManager:
    """
    配置管理器单例

    - 启动时从数据库加载到内存缓存
    - 读取操作直接访问内存（同步）
    - 写入操作同时更新数据库和内存（异步）
    """

    _instance: Optional["ConfigManager"] = None

    # 默认配置定义: key -> (type, default_value, description)
    CONFIG_DEFAULTS: Dict[str, tuple] = {
        "proxy.address": ("str", "", "代理地址 host:port"),
        "proxy.enabled": ("bool", True, "是否启用代理"),
        "proxy.hosts": (
            "json",
            [
                "accounts.nintendo.com",
                "api.accounts.nintendo.com",
                "api-lp1.znc.srv.nintendo.net",
            ],
            "需要代理的主机列表",
        ),
        "http.timeout": ("float", 60.0, "HTTP 请求超时秒数"),
    }

    def __init__(self):
        self._cache: Dict[str, Any] = {}
        self._types: Dict[str, str] = {}
        self._initialized = False
        self._lock = asyncio.Lock()

    @classmethod
    def instance(cls) -> "ConfigManager":
        """获取单例实例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def ensure_defaults(self) -> None:
        """确保默认配置存在（首次运行时初始化）"""
        async with self._lock:
            # 使用 ORM 元数据创建表
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

            async with get_session() as session:
                # 批量获取现有配置以减少查询
                existing = await ConfigDAO.get_all(session)
                existing_keys = {e.key for e in existing}

                # 检查并插入缺失的默认配置
                for key, (type_, default, desc) in self.CONFIG_DEFAULTS.items():
                    if key not in existing_keys:
                        env_val = self._get_env_override(key)
                        value = env_val if env_val is not None else default
                        await ConfigDAO.set(session, key, value, type_, desc)
                        logger.info(f"Config initialized: {key} = {value}")

    def _get_env_override(self, key: str) -> Optional[Any]:
        """从环境变量获取覆盖值"""
        env_map = {
            "proxy.address": "SPLATOON3_PROXY_ADDRESS",
            "http.timeout": "SPLATOON3_HTTP_TIMEOUT",
        }
        env_key = env_map.get(key)
        if env_key:
            val = os.environ.get(env_key)
            if val:
                type_ = self.CONFIG_DEFAULTS[key][0]
                try:
                    return self._parse_env_value(val, type_)
                except (ValueError, json.JSONDecodeError) as e:
                    logger.warning(f"Invalid env value for {key}: {e}")
        return None

    @staticmethod
    def _parse_env_value(val: str, type_: str) -> Any:
        """解析环境变量值"""
        if type_ == "int":
            return int(val)
        if type_ == "float":
            return float(val)
        if type_ == "bool":
            return val.lower() in ("true", "1", "yes")
        if type_ == "json":
            return json.loads(val)
        return val

    async def load(self) -> None:
        """从数据库加载配置到内存"""
        async with self._lock:
            async with get_session() as session:
                entries = await ConfigDAO.get_all(session)
                self._cache.clear()
                self._types.clear()
                for entry in entries:
                    self._cache[entry.key] = ConfigDAO._deserialize(
                        entry.value, entry.type
                    )
                    self._types[entry.key] = entry.type
                self._initialized = True
                logger.info(f"Config loaded: {len(self._cache)} entries")

    def _resolve_type(self, key: str, value: Any) -> str:
        """根据已有定义或实际值确定存储类型"""
        if key in self.CONFIG_DEFAULTS:
            return self.CONFIG_DEFAULTS[key][0]
        if key in self._types:
            return self._types[key]
        return self._infer_type(value)

    def _validate_type(self, key: str, value: Any, type_: str) -> None:
        """验证值类型"""
        if value is None:
            return
        if type_ == "int" and not isinstance(value, int):
            raise ValueError(f"Config '{key}' expects int, got {type(value).__name__}")
        if type_ == "float" and not isinstance(value, (int, float)):
            raise ValueError(f"Config '{key}' expects float, got {type(value).__name__}")
        if type_ == "bool" and not isinstance(value, bool):
            raise ValueError(f"Config '{key}' expects bool, got {type(value).__name__}")
        if type_ == "json" and not isinstance(value, (list, dict)):
            raise ValueError(f"Config '{key}' expects list/dict, got {type(value).__name__}")

    async def set(self, key: str, value: Any) -> None:
        """设置配置值（同时更新数据库和内存）"""
        type_ = self._resolve_type(key, value)
        self._validate_type(key, value, type_)

        async with self._lock:
            async with get_session() as session:
                await ConfigDAO.set(session, key, value, type_)
            self._cache[key] = value
            self._types[key] = type_
            logger.debug(f"Config updated: {key} = {value}")

    async def set_many(self, items: List[Tuple[str, Any]]) -> None:
        """批量设置配置（单事务，原子性）"""
        # 先验证所有项
        validated = []
        for key, value in items:
            type_ = self._resolve_type(key, value)
            self._validate_type(key, value, type_)
            validated.append((key, value, type_))

        async with self._lock:
            async with get_session() as session:
                for key, value, type_ in validated:
                    await ConfigDAO.set(session, key, value, type_)
            # 事务成功后更新缓存
            for key, value, type_ in validated:
                self._cache[key] = value
                self._types[key] = type_
            logger.debug(f"Config bulk updated: {[k for k, _, _ in validated]}")

    @staticmethod
    def _infer_type(value: Any) -> str:
        """推断值类型"""
        if isinstance(value, bool):
            return "bool"
        if isinstance(value, int):
            return "int"
        if isinstance(value, float):
            return "float"
        if isinstance(value, (list, dict)):
            return "json"
        return "str"

    # ===== 同步读取方法（直接访问内存缓存）=====

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        if key in self._cache:
            return self._cache[key]
        if key in self.CONFIG_DEFAULTS:
            return self.CONFIG_DEFAULTS[key][1]
        return default

    def get_str(self, key: str, default: str = "") -> str:
        """获取字符串配置"""
        val = self.get(key, default)
        return str(val) if val is not None else default

    def get_int(self, key: str, default: int = 0) -> int:
        """获取整数配置"""
        val = self.get(key, default)
        try:
            return int(val) if val is not None else default
        except (ValueError, TypeError):
            return default

    def get_float(self, key: str, default: float = 0.0) -> float:
        """获取浮点数配置"""
        val = self.get(key, default)
        try:
            return float(val) if val is not None else default
        except (ValueError, TypeError):
            return default

    def get_bool(self, key: str, default: bool = False) -> bool:
        """获取布尔配置"""
        val = self.get(key, default)
        if isinstance(val, bool):
            return val
        if isinstance(val, str):
            return val.lower() in ("true", "1", "yes")
        return default

    def get_json(self, key: str, default: Any = None) -> Any:
        """获取 JSON 配置（列表/字典）"""
        return self.get(key, default if default is not None else [])

    def get_all(self) -> Dict[str, Any]:
        """获取所有配置"""
        result = {}
        for key, (_, default, _) in self.CONFIG_DEFAULTS.items():
            result[key] = default
        result.update(self._cache)
        return result

    def get_all_with_meta(self) -> List[Dict[str, Any]]:
        """获取所有配置（含元数据）"""
        result = []
        all_keys = set(self.CONFIG_DEFAULTS.keys()) | set(self._cache.keys())
        for key in sorted(all_keys):
            type_ = self._types.get(key, self.CONFIG_DEFAULTS.get(key, ("str",))[0])
            desc = self.CONFIG_DEFAULTS.get(key, (None, None, None))[2]
            result.append({
                "key": key,
                "value": self.get(key),
                "type": type_,
                "description": desc,
            })
        return result
