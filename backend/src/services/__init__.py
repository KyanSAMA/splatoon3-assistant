"""服务模块 - FastAPI 路由"""

from .auth_service import router as auth_router

__all__ = [
    "auth_router",
]
