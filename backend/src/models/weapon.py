"""武器数据模型"""

from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class SubWeapon:
    """副武器"""
    id: int
    code: str
    ink_consume: Optional[float]
    zh_name: Optional[str]
    params: Optional[str]
    created_at: str

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> Optional["SubWeapon"]:
        if not data:
            return None
        return cls(
            id=data.get("id", 0),
            code=data.get("code", ""),
            ink_consume=data.get("ink_consume"),
            zh_name=data.get("zh_name"),
            params=data.get("params"),
            created_at=data.get("created_at", ""),
        )


@dataclass
class SpecialWeapon:
    """特殊武器"""
    id: int
    code: str
    zh_name: Optional[str]
    params: Optional[str]
    created_at: str

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> Optional["SpecialWeapon"]:
        if not data:
            return None
        return cls(
            id=data.get("id", 0),
            code=data.get("code", ""),
            zh_name=data.get("zh_name"),
            params=data.get("params"),
            created_at=data.get("created_at", ""),
        )


@dataclass
class MainWeapon:
    """主武器"""
    id: int
    code: str
    special_point: int
    sub_weapon_code: Optional[str]
    special_weapon_code: Optional[str]
    zh_name: Optional[str]
    weapon_class: Optional[str]
    distance_class: Optional[str]
    params: Optional[str]
    created_at: str

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> Optional["MainWeapon"]:
        if not data:
            return None
        return cls(
            id=data.get("id", 0),
            code=data.get("code", ""),
            special_point=data.get("special_point", 0),
            sub_weapon_code=data.get("sub_weapon_code"),
            special_weapon_code=data.get("special_weapon_code"),
            zh_name=data.get("zh_name"),
            weapon_class=data.get("weapon_class"),
            distance_class=data.get("distance_class"),
            params=data.get("params"),
            created_at=data.get("created_at", ""),
        )
