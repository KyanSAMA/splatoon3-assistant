"""Splatoon3 Assistant API 入口"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.services import auth_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    yield


app = FastAPI(
    title="Splatoon3 Assistant",
    description="Splatoon3 游戏数据分析助手 API",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(auth_router)


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "ok"}
