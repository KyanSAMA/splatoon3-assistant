"""配置 DAO"""

import json
import logging
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.dao.models.config import ConfigEntry

logger = logging.getLogger(__name__)


class ConfigDAO:
    """配置数据访问对象"""

    @staticmethod
    def _parse_bool(value: Any) -> bool:
        """严格解析布尔值"""
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.strip().lower() in ("true", "1", "yes", "y", "on")
        return bool(value)

    @staticmethod
    def _serialize(value: Any, type_: str) -> Optional[str]:
        """序列化值为字符串"""
        if value is None:
            return None
        if type_ == "json":
            return json.dumps(value, ensure_ascii=False)
        if type_ == "bool":
            return "true" if ConfigDAO._parse_bool(value) else "false"
        return str(value)

    @staticmethod
    def _deserialize(value: Optional[str], type_: str) -> Any:
        """反序列化字符串为对应类型"""
        if value is None:
            return None
        try:
            if type_ == "int":
                return int(value)
            if type_ == "float":
                return float(value)
            if type_ == "bool":
                return ConfigDAO._parse_bool(value)
            if type_ == "json":
                return json.loads(value)
        except (ValueError, TypeError, json.JSONDecodeError) as e:
            logger.warning(f"Failed to deserialize '{value}' as {type_}: {e}")
            return value
        return value

    @staticmethod
    async def get_all(session: AsyncSession) -> List[ConfigEntry]:
        """获取所有配置项"""
        result = await session.execute(select(ConfigEntry))
        return list(result.scalars().all())

    @staticmethod
    async def get_all_as_dict(session: AsyncSession) -> Dict[str, Any]:
        """获取所有配置并转换为字典"""
        entries = await ConfigDAO.get_all(session)
        return {
            e.key: ConfigDAO._deserialize(e.value, e.type)
            for e in entries
        }

    @staticmethod
    async def get(session: AsyncSession, key: str) -> Optional[ConfigEntry]:
        """获取单个配置项"""
        result = await session.execute(
            select(ConfigEntry).where(ConfigEntry.key == key)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def set(
        session: AsyncSession,
        key: str,
        value: Any,
        type_: str = "str",
        description: Optional[str] = None,
    ) -> ConfigEntry:
        """设置配置项（存在则更新，不存在则插入）"""
        entry = await ConfigDAO.get(session, key)
        str_val = ConfigDAO._serialize(value, type_)

        if entry:
            entry.value = str_val
            entry.type = type_
            if description is not None:
                entry.description = description
        else:
            entry = ConfigEntry(
                key=key, value=str_val, type=type_, description=description
            )
            session.add(entry)

        return entry

    @staticmethod
    async def delete(session: AsyncSession, key: str) -> bool:
        """删除配置项"""
        entry = await ConfigDAO.get(session, key)
        if entry:
            await session.delete(entry)
            return True
        return False
