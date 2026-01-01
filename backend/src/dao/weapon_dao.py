"""武器数据访问层 (DAO) - SQLAlchemy 2.0 (保留原 SQL)"""

import json
from typing import Optional, List, Dict, Any

from sqlalchemy import text

from .database import get_session

_WEAPON_FULL_SQL = """
SELECT
    m.id,
    m.code,
    m.zh_name AS weapon_name,
    m.weapon_class,
    m.distance_class,
    m.special_point,
    m.params AS weapon_params,
    s.code AS sub_code,
    s.zh_name AS sub_name,
    s.ink_consume AS sub_ink_consume,
    s.params AS sub_params,
    sp.code AS special_code,
    sp.zh_name AS special_name,
    sp.params AS special_params
FROM main_weapon m
LEFT JOIN sub_weapon s ON m.sub_weapon_code = s.code
LEFT JOIN special_weapon sp ON m.special_weapon_code = sp.code
"""

_WEAPON_BRIEF_SQL = """
SELECT
    m.code,
    m.zh_name AS weapon_name,
    m.weapon_class,
    m.special_point,
    s.zh_name AS sub_name,
    sp.zh_name AS special_name
FROM main_weapon m
LEFT JOIN sub_weapon s ON m.sub_weapon_code = s.code
LEFT JOIN special_weapon sp ON m.special_weapon_code = sp.code
"""

_JSON_COLS = ("weapon_params", "sub_params", "special_params", "params")


def _like_pattern(value: str) -> str:
    return f"%{value}%"


def _parse_json(val: Any) -> Any:
    if val is None or isinstance(val, (dict, list)):
        return val
    if isinstance(val, (bytes, bytearray)):
        val = val.decode("utf-8")
    if isinstance(val, str):
        try:
            return json.loads(val)
        except json.JSONDecodeError:
            return val
    return val


def _deserialize(row: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if row is None:
        return None
    for col in _JSON_COLS:
        if col in row:
            row[col] = _parse_json(row[col])
    return row


def _safe_limit(limit: int) -> int:
    return max(1, limit)


async def _fetch_one(sql: str, params: dict) -> Optional[Dict[str, Any]]:
    async with get_session() as session:
        result = await session.execute(text(sql), params)
        row = result.mappings().first()
        return _deserialize(dict(row)) if row else None


async def _fetch_all(sql: str, params: dict) -> List[Dict[str, Any]]:
    async with get_session() as session:
        result = await session.execute(text(sql), params)
        rows = result.mappings().all()
        return [_deserialize(dict(r)) for r in rows]


async def get_weapon_by_name(weapon_name: str) -> Optional[Dict[str, Any]]:
    sql = _WEAPON_FULL_SQL + "WHERE m.zh_name LIKE :pattern COLLATE NOCASE ORDER BY m.code LIMIT 1"
    return await _fetch_one(sql, {"pattern": _like_pattern(weapon_name)})


async def search_weapons_by_name(weapon_name: str, limit: int = 10) -> List[Dict[str, Any]]:
    sql = _WEAPON_FULL_SQL + "WHERE m.zh_name LIKE :pattern COLLATE NOCASE ORDER BY m.code LIMIT :limit"
    return await _fetch_all(sql, {"pattern": _like_pattern(weapon_name), "limit": _safe_limit(limit)})


async def get_weapons_by_sub(sub_name: str) -> List[Dict[str, Any]]:
    sql = _WEAPON_BRIEF_SQL + "WHERE s.zh_name LIKE :pattern COLLATE NOCASE ORDER BY m.code"
    return await _fetch_all(sql, {"pattern": _like_pattern(sub_name)})


async def get_weapons_by_special(special_name: str) -> List[Dict[str, Any]]:
    sql = _WEAPON_BRIEF_SQL + "WHERE sp.zh_name LIKE :pattern COLLATE NOCASE ORDER BY m.code"
    return await _fetch_all(sql, {"pattern": _like_pattern(special_name)})


async def get_all_weapons(limit: int = 100) -> List[Dict[str, Any]]:
    sql = _WEAPON_BRIEF_SQL + "ORDER BY m.code LIMIT :limit"
    return await _fetch_all(sql, {"limit": _safe_limit(limit)})


async def get_weapon_by_code(code: str) -> Optional[Dict[str, Any]]:
    sql = _WEAPON_FULL_SQL + "WHERE m.code = :code"
    return await _fetch_one(sql, {"code": code})


async def get_weapon_by_id(weapon_id: int) -> Optional[Dict[str, Any]]:
    sql = _WEAPON_FULL_SQL + "WHERE m.id = :id"
    return await _fetch_one(sql, {"id": weapon_id})


async def get_all_main_weapons() -> List[Dict[str, Any]]:
    """获取所有主武器"""
    sql = """
    SELECT id, code, zh_name, weapon_class, sub_weapon_code, special_weapon_code, special_point
    FROM main_weapon ORDER BY code
    """
    return await _fetch_all(sql, {})


async def get_all_sub_weapons() -> List[Dict[str, Any]]:
    """获取所有副武器"""
    sql = "SELECT id, code, zh_name FROM sub_weapon ORDER BY code"
    return await _fetch_all(sql, {})


async def get_all_special_weapons() -> List[Dict[str, Any]]:
    """获取所有特殊武器"""
    sql = "SELECT id, code, zh_name FROM special_weapon ORDER BY code"
    return await _fetch_all(sql, {})
