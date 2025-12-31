"""数据模型定义"""

from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class User:
    """本地用户"""
    id: int
    nsa_id: str
    splatoon_id: Optional[str]
    session_token: str
    access_token: str
    g_token: str
    bullet_token: str
    user_lang: str
    user_country: str
    user_nickname: Optional[str]
    is_current: bool
    session_expired: bool
    last_login_at: str
    created_at: str
    updated_at: str

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> Optional["User"]:
        """从字典创建 User 对象"""
        if not data:
            return None
        return cls(
            id=data.get("id", 0),
            nsa_id=data.get("nsa_id", ""),
            splatoon_id=data.get("splatoon_id"),
            session_token=data.get("session_token", ""),
            access_token=data.get("access_token", ""),
            g_token=data.get("g_token", ""),
            bullet_token=data.get("bullet_token", ""),
            user_lang=data.get("user_lang", "zh-CN"),
            user_country=data.get("user_country", "JP"),
            user_nickname=data.get("user_nickname"),
            is_current=bool(data.get("is_current", 0)),
            session_expired=bool(data.get("session_expired", 0)),
            last_login_at=data.get("last_login_at", ""),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
        )

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典（不含敏感 token）"""
        return {
            "id": self.id,
            "nsa_id": self.nsa_id,
            "splatoon_id": self.splatoon_id,
            "user_lang": self.user_lang,
            "user_country": self.user_country,
            "user_nickname": self.user_nickname,
            "is_current": self.is_current,
            "last_login_at": self.last_login_at,
            "created_at": self.created_at,
        }