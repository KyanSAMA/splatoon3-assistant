"""技能数据模型"""

from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class Skill:
    """装备能力"""
    id: int
    code: str
    zh_name: Optional[str]
    zh_desc: Optional[str]
    created_at: str

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> Optional["Skill"]:
        if not data:
            return None
        return cls(
            id=data.get("id", 0),
            code=data.get("code", ""),
            zh_name=data.get("zh_name"),
            zh_desc=data.get("zh_desc"),
            created_at=data.get("created_at", ""),
        )
