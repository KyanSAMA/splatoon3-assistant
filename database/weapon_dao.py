"""武器数据访问层 (DAO)"""

import json
from typing import Optional, List, Dict, Any

from .connect import get_cursor

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


async def _fetch_one(sql: str, params: tuple) -> Optional[Dict[str, Any]]:
    async with get_cursor() as cursor:
        await cursor.execute(sql, params)
        row = await cursor.fetchone()
    return _deserialize(row)


async def _fetch_all(sql: str, params: tuple) -> List[Dict[str, Any]]:
    async with get_cursor() as cursor:
        await cursor.execute(sql, params)
        rows = await cursor.fetchall()
    return [_deserialize(r) for r in rows]


async def get_weapon_by_name(weapon_name: str) -> Optional[Dict[str, Any]]:
    sql = _WEAPON_FULL_SQL + "WHERE m.zh_name LIKE ? COLLATE NOCASE ORDER BY m.code LIMIT 1"
    return await _fetch_one(sql, (_like_pattern(weapon_name),))


async def search_weapons_by_name(weapon_name: str, limit: int = 10) -> List[Dict[str, Any]]:
    sql = _WEAPON_FULL_SQL + "WHERE m.zh_name LIKE ? COLLATE NOCASE ORDER BY m.code LIMIT ?"
    return await _fetch_all(sql, (_like_pattern(weapon_name), _safe_limit(limit)))


async def get_weapons_by_sub(sub_name: str) -> List[Dict[str, Any]]:
    sql = _WEAPON_BRIEF_SQL + "WHERE s.zh_name LIKE ? COLLATE NOCASE ORDER BY m.code"
    return await _fetch_all(sql, (_like_pattern(sub_name),))


async def get_weapons_by_special(special_name: str) -> List[Dict[str, Any]]:
    sql = _WEAPON_BRIEF_SQL + "WHERE sp.zh_name LIKE ? COLLATE NOCASE ORDER BY m.code"
    return await _fetch_all(sql, (_like_pattern(special_name),))


async def get_all_weapons(limit: int = 100) -> List[Dict[str, Any]]:
    sql = _WEAPON_BRIEF_SQL + "ORDER BY m.code LIMIT ?"
    return await _fetch_all(sql, (_safe_limit(limit),))


async def get_weapon_by_code(code: str) -> Optional[Dict[str, Any]]:
    sql = _WEAPON_FULL_SQL + "WHERE m.code = ?"
    return await _fetch_one(sql, (code,))
