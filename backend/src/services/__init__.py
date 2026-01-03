"""服务模块 - FastAPI 路由"""

from .auth_service import router as auth_router
from .auth_service import (
    require_current_user,
    require_splatnet_api,
    close_user_api_session,
    close_all_api_sessions,
)
from .splatoon3_data_refresh_service import router as data_router
from .battle_detail_refresh_service import router as battle_refresh_router
from .battle_service import router as battle_query_router
from .coop_detail_refresh_service import router as coop_router
from .coop_service import router as coop_query_router
from .stage_service import router as stage_router
from .config_service import router as config_router
from .data_service import router as backup_router

__all__ = [
    "auth_router",
    "data_router",
    "battle_refresh_router",
    "battle_query_router",
    "coop_router",
    "coop_query_router",
    "stage_router",
    "config_router",
    "backup_router",
    "require_current_user",
    "require_splatnet_api",
    "close_user_api_session",
    "close_all_api_sessions",
]
