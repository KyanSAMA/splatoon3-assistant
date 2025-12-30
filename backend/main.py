"""Splatoon3 Assistant API 入口"""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from src.services import auth_router, data_router, battle_router, coop_router, stage_router, close_all_api_sessions

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info("Application starting...")
    yield
    # 关闭时清理所有 API 会话
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
app.include_router(battle_router)
app.include_router(coop_router)
app.include_router(stage_router)

# 静态文件服务 - 地图图片
stage_images_path = Path(__file__).parent.parent / "data" / "images" / "stage"
if stage_images_path.exists():
    app.mount("/static/stage", StaticFiles(directory=str(stage_images_path)), name="stage_images")

# 静态文件服务 - 武器图片
weapon_images_path = Path(__file__).parent.parent / "data" / "images" / "main_weapon"
if weapon_images_path.exists():
    app.mount("/static/weapon", StaticFiles(directory=str(weapon_images_path)), name="weapon_images")

# 静态文件服务 - 规则图标
vs_rule_images_path = Path(__file__).parent.parent / "data" / "images" / "vs_rule"
if vs_rule_images_path.exists():
    app.mount("/static/vs_rule", StaticFiles(directory=str(vs_rule_images_path)), name="vs_rule_images")


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "ok"}
