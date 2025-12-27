# Token 持久化存储模块
"""
提供 Token 的持久化存储功能，支持读取、写入和重载
"""

import json
import os
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path


class TokenStore:
    """
    Token 持久化存储类

    使用 JSON 文件存储 token 信息，支持原子写入（避免部分写入）

    存储格式:
    {
        "session_token": "...",
        "g_token": "...",
        "bullet_token": "...",
        "access_token": "...",
        "user_lang": "zh-CN",
        "user_country": "JP",
        "user_nickname": "...",
        "user_info": {...},
        "updated_at": "2024-01-01T00:00:00"
    }
    """

    def __init__(self, file_path: str = ".token_cache.json"):
        """
        初始化 TokenStore

        Args:
            file_path: Token 缓存文件路径（默认为当前目录下的 .token_cache.json）
        """
        self.file_path = Path(file_path)
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        """确保文件存在，如果不存在则创建空文件"""
        if not self.file_path.exists():
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            self.save({})
    def exists(self):
        """是否存在缓存文件"""
        return self.file_path.exists()

    def load(self) -> Dict[str, Any]:
        """
        从文件加载 token 信息

        Returns:
            包含 token 信息的字典，如果文件不存在或解析失败则返回空字典
        """
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"[TokenStore] Failed to load tokens: {e}")
            return {}

    def save(self, data: Dict[str, Any]):
        """
        保存 token 信息到文件（原子写入）

        Args:
            data: 要保存的 token 信息字典
        """
        # 添加更新时间
        data["updated_at"] = datetime.utcnow().isoformat()

        # 原子写入：先写入临时文件，再重命名
        temp_file = self.file_path.with_suffix('.tmp')
        try:
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            # 原子操作：rename 在大多数系统上是原子的
            temp_file.replace(self.file_path)
        except Exception as e:
            print(f"[TokenStore] Failed to save tokens: {e}")
            if temp_file.exists():
                temp_file.unlink()
            raise

    def update(self, **kwargs):
        """
        更新部分字段（保留其他字段）

        Args:
            **kwargs: 要更新的字段
        """
        data = self.load()
        data.update(kwargs)
        self.save(data)

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取指定字段的值

        Args:
            key: 字段名
            default: 默认值

        Returns:
            字段值，如果不存在则返回 default
        """
        data = self.load()
        return data.get(key, default)

    def clear(self):
        """清空所有 token 信息"""
        self.save({})

    def has_valid_session(self) -> bool:
        """
        检查是否有有效的 session_token

        Returns:
            如果存在 session_token 则返回 True
        """
        return bool(self.get("session_token"))

    def has_valid_tokens(self) -> bool:
        """
        检查是否有完整的 token 信息

        Returns:
            如果同时存在 g_token 和 bullet_token 则返回 True
        """
        data = self.load()
        return bool(data.get("g_token") and data.get("bullet_token"))

    def get_tokens_for_api(self) -> tuple[Optional[str], Optional[str], str, str]:
        """
        获取用于 API 调用的 token 信息

        Returns:
            (g_token, bullet_token, user_lang, user_country)
        """
        data = self.load()
        return (
            data.get("session_token"),
            data.get("access_token"),
            data.get("g_token"),
            data.get("bullet_token"),
            data.get("user_lang", "zh-CN"),
            data.get("user_country", "JP"),
        )
