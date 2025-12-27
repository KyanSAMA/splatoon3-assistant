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
from .user_dao import (
    TokenBundle,
    get_current_user,
    get_user_by_id,
    get_user_by_splatoon_id,
    get_user_by_nsa_id,
    get_user_by_session_token,
    get_all_users,
    create_or_update_user,
    update_tokens,
    set_current_user,
    delete_user,
    clear_current_user,
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
    "TokenBundle",
    "get_current_user",
    "get_user_by_id",
    "get_user_by_splatoon_id",
    "get_user_by_nsa_id",
    "get_user_by_session_token",
    "get_all_users",
    "create_or_update_user",
    "update_tokens",
    "set_current_user",
    "delete_user",
    "clear_current_user",
]
