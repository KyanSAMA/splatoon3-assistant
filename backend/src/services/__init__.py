"""服务模块 - FastAPI 路由"""

from .auth_service import router as auth_router
from .auth_service import (
    require_current_user,
    require_splatnet_api,
    close_user_api_session,
    close_all_api_sessions,
)
from .splatoon3_data_refresh_service import router as data_router
from .battle_detail_refresh_service import router as battle_router

__all__ = [
    "auth_router",
    "data_router",
    "battle_router",
    "require_current_user",
    "require_splatnet_api",
    "close_user_api_session",
    "close_all_api_sessions",
]
