# Splatoon3 Assistant
"""
Splatoon3 游戏助手 - 通过获取 Splatoon3 的战斗数据及其他辅助数据进行数据分析
"""

from .core import (
    Config,
    default_config,
    HttpClient,
    AsyncHttpClient,
    SplatoonError,
    SessionExpiredError,
    MembershipRequiredError,
    BulletTokenError,
    NetworkError,
    TokenRefreshError,
)
from .auth import NSOAuth, TokenStore
from .api import SplatNet3API
from .models import User
from .services import auth_router

__all__ = [
    # Core
    "Config",
    "default_config",
    "HttpClient",
    "AsyncHttpClient",
    # Auth
    "NSOAuth",
    "TokenStore",
    # API
    "SplatNet3API",
    # Models
    "User",
    # Services (FastAPI Routers)
    "auth_router",
    # Exceptions
    "SplatoonError",
    "SessionExpiredError",
    "MembershipRequiredError",
    "BulletTokenError",
    "NetworkError",
    "TokenRefreshError",
]
