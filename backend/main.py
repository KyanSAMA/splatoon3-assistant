"""Splatoon3 Assistant API 入口"""

import logging
import os
import sys
import webbrowser
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from src.core.config_manager import ConfigManager
from src.core.migration_manager import init_database
from src.dao.database import DB_PATH
from src.services import (
    auth_router,
    data_router,
    battle_refresh_router,
    battle_query_router,
    coop_router,
    coop_query_router,
    stage_router,
    config_router,
    backup_router,
    close_all_api_sessions,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_frontend_path() -> Path | None:
    """获取前端静态文件路径"""
    if getattr(sys, 'frozen', False):
        base = Path(getattr(sys, '_MEIPASS', '.'))
        return base / "frontend" / "dist"
    else:
        return Path(__file__).resolve().parent.parent / "frontend" / "dist"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info("=" * 40)
    logger.info("  数据初始化中，请耐心等待...")
    logger.info("=" * 40)

    # 初始化数据库（自动迁移）
    await init_database(DB_PATH)

    # 初始化配置管理器
    mgr = ConfigManager.instance()
    await mgr.ensure_defaults()
    await mgr.load()
    logger.info("初始化完成，服务已就绪")

    # 初始化完成后打开浏览器
    app_url = os.environ.get("APP_URL")
    if app_url:
        webbrowser.open(app_url)

    yield

    logger.info("Application shutting down, cleaning up...")
    await close_all_api_sessions()


app = FastAPI(
    title="Splatoon3 Assistant",
    description="Splatoon3 游戏数据分析助手 API",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(auth_router, prefix="/api")
app.include_router(data_router, prefix="/api")
app.include_router(battle_refresh_router, prefix="/api")
app.include_router(battle_query_router, prefix="/api")
app.include_router(coop_router, prefix="/api")
app.include_router(coop_query_router, prefix="/api")
app.include_router(stage_router, prefix="/api")
app.include_router(config_router, prefix="/api")
app.include_router(backup_router, prefix="/api")


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "ok"}


# 前端静态文件挂载
_frontend_path = get_frontend_path()
if _frontend_path and _frontend_path.exists():
    _index_html = _frontend_path / "index.html"

    app.mount("/assets", StaticFiles(directory=_frontend_path / "assets"), name="assets")
    app.mount("/static", StaticFiles(directory=_frontend_path / "static"), name="static")

    @app.get("/{path:path}")
    async def serve_spa(path: str):
        """SPA 路由回退"""
        file_path = (_frontend_path / path).resolve()
        base_path = _frontend_path.resolve()
        if file_path.is_relative_to(base_path) and file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(_index_html)
