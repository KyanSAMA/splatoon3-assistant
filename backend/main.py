"""Splatoon3 Assistant API 入口"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.core.config_manager import ConfigManager
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


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info("Application starting...")

    # 初始化配置管理器
    mgr = ConfigManager.instance()
    await mgr.ensure_defaults()
    await mgr.load()
    logger.info("Configuration loaded")

    yield

    logger.info("Application shutting down, cleaning up...")
    await close_all_api_sessions()


app = FastAPI(
    title="Splatoon3 Assistant",
    description="Splatoon3 游戏数据分析助手 API",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(auth_router)
app.include_router(data_router)
app.include_router(battle_refresh_router)
app.include_router(battle_query_router)
app.include_router(coop_router)
app.include_router(coop_query_router)
app.include_router(stage_router)
app.include_router(config_router)
app.include_router(backup_router)


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "ok"}
