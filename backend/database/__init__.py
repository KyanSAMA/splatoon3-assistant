"""Database module for Splatoon3 Assistant"""

from .connect import get_connection, get_cursor
from .weapon_dao import (
    get_weapon_by_name,
    search_weapons_by_name,
    get_weapons_by_sub,
    get_weapons_by_special,
    get_all_weapons,
    get_weapon_by_code,
)

__all__ = [
    "get_connection",
    "get_cursor",
    "get_weapon_by_name",
    "search_weapons_by_name",
    "get_weapons_by_sub",
    "get_weapons_by_special",
    "get_all_weapons",
    "get_weapon_by_code",
]
