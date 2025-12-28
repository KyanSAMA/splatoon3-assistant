"""地图数据模型"""

from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class Stage:
    """地图"""
    id: int
    vs_stage_id: Optional[int]
    code: str
    zh_name: Optional[str]
    stage_type: Optional[str]  # 'VS' | 'Coop'
    created_at: str

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> Optional["Stage"]:
        if not data:
            return None
        return cls(
            id=data.get("id", 0),
            vs_stage_id=data.get("vs_stage_id"),
            code=data.get("code", ""),
            zh_name=data.get("zh_name"),
            stage_type=data.get("stage_type"),
            created_at=data.get("created_at", ""),
        )
