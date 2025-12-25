"""武器数据访问层 (DAO)"""

from typing import Optional, List, Dict, Any

from pool import get_cursor

# 武器完整信息查询 SQL（复用）
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
FROM main_weapons m
LEFT JOIN sub_weapons s ON m.sub_weapon_code = s.code
LEFT JOIN special_weapons sp ON m.special_weapon_code = sp.code
"""

# 武器简要信息查询 SQL
_WEAPON_BRIEF_SQL = """
SELECT
    m.code,
    m.zh_name AS weapon_name,
    m.weapon_class,
    m.special_point,
    s.zh_name AS sub_name,
    sp.zh_name AS special_name
FROM main_weapons m
LEFT JOIN sub_weapons s ON m.sub_weapon_code = s.code
LEFT JOIN special_weapons sp ON m.special_weapon_code = sp.code
"""


def _like_pattern(value: str) -> str:
    """构建 ILIKE 模糊匹配模式"""
    return f"%{value}%"


def _fetch_one(sql: str, params: tuple) -> Optional[Dict[str, Any]]:
    """执行查询并返回单条记录"""
    with get_cursor() as cursor:
        cursor.execute(sql, params)
        return cursor.fetchone()


def _fetch_all(sql: str, params: tuple) -> List[Dict[str, Any]]:
    """执行查询并返回所有记录"""
    with get_cursor() as cursor:
        cursor.execute(sql, params)
        return cursor.fetchall()


def _safe_limit(limit: int) -> int:
    """确保 limit 为正整数，防止全表扫描"""
    return max(1, limit)


def get_weapon_by_name(weapon_name: str) -> Optional[Dict[str, Any]]:
    """
    根据武器名称获取武器信息（包含副武器和特殊武器）

    Args:
        weapon_name: 武器中文名称（支持模糊匹配）

    Returns:
        包含主武器、副武器、特殊武器信息的字典，未找到返回 None
    """
    sql = _WEAPON_FULL_SQL + "WHERE m.zh_name ILIKE %s ORDER BY m.code LIMIT 1"
    return _fetch_one(sql, (_like_pattern(weapon_name),))


def search_weapons_by_name(weapon_name: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    根据武器名称搜索武器列表（包含副武器和特殊武器）

    Args:
        weapon_name: 武器中文名称（支持模糊匹配）
        limit: 返回结果数量限制

    Returns:
        武器信息字典列表
    """
    sql = _WEAPON_FULL_SQL + "WHERE m.zh_name ILIKE %s ORDER BY m.code LIMIT %s"
    return _fetch_all(sql, (_like_pattern(weapon_name), _safe_limit(limit)))


def get_weapons_by_sub(sub_name: str) -> List[Dict[str, Any]]:
    """
    根据副武器名称获取所有使用该副武器的主武器

    Args:
        sub_name: 副武器中文名称（支持模糊匹配）

    Returns:
        武器信息字典列表
    """
    sql = _WEAPON_BRIEF_SQL + "WHERE s.zh_name ILIKE %s ORDER BY m.code"
    return _fetch_all(sql, (_like_pattern(sub_name),))


def get_weapons_by_special(special_name: str) -> List[Dict[str, Any]]:
    """
    根据特殊武器名称获取所有使用该特殊武器的主武器

    Args:
        special_name: 特殊武器中文名称（支持模糊匹配）

    Returns:
        武器信息字典列表
    """
    sql = _WEAPON_BRIEF_SQL + "WHERE sp.zh_name ILIKE %s ORDER BY m.code"
    return _fetch_all(sql, (_like_pattern(special_name),))


def get_all_weapons(limit: int = 100) -> List[Dict[str, Any]]:
    """
    获取所有武器列表

    Args:
        limit: 返回结果数量限制

    Returns:
        武器信息字典列表
    """
    sql = _WEAPON_BRIEF_SQL + "ORDER BY m.code LIMIT %s"
    return _fetch_all(sql, (_safe_limit(limit),))


def get_weapon_by_code(code: str) -> Optional[Dict[str, Any]]:
    """
    根据武器代码精确获取武器信息

    Args:
        code: 武器代码

    Returns:
        武器信息字典，未找到返回 None
    """
    sql = _WEAPON_FULL_SQL + "WHERE m.code = %s"
    return _fetch_one(sql, (code,))
