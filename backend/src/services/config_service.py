"""配置管理 API"""

import asyncio
from typing import Any, Dict, List, Tuple

import httpx
from fastapi import APIRouter, Body, HTTPException
from pydantic import BaseModel

from src.core.config import Config
from src.core.config_manager import ConfigManager

router = APIRouter(prefix="/config", tags=["config"])

CONNECTIVITY_TIMEOUT = 5.0


class ConfigItem(BaseModel):
    """配置项"""
    key: str
    value: Any
    type: str
    description: str | None = None


class ConfigUpdate(BaseModel):
    """配置更新请求"""
    key: str
    value: Any


class ConnectivityResult(BaseModel):
    """连通性检查结果"""
    reachable: bool
    failed_hosts: List[str]
    message: str


async def _check_host(host: str, config: Config) -> Tuple[str, bool]:
    """检查单个主机是否可达"""
    url = f"https://{host}" if not host.startswith("http") else host
    proxy = config.proxies if config.should_use_proxy(host) else None

    try:
        async with httpx.AsyncClient(
            proxy=proxy, timeout=CONNECTIVITY_TIMEOUT, http2=True
        ) as client:
            await client.head(url)
        return host, True
    except Exception:
        return host, False


@router.get("", response_model=Dict[str, Any])
async def get_config():
    """获取所有配置（简单键值对）"""
    mgr = ConfigManager.instance()
    return mgr.get_all()


@router.get("/details", response_model=List[ConfigItem])
async def get_config_details():
    """获取所有配置（含类型和描述）"""
    mgr = ConfigManager.instance()
    return mgr.get_all_with_meta()


@router.patch("", response_model=Dict[str, Any])
async def update_config(updates: List[ConfigUpdate]):
    """批量更新配置（原子性操作）"""
    mgr = ConfigManager.instance()
    errors = []
    pending = []

    for update in updates:
        if update.key not in mgr.CONFIG_DEFAULTS and update.key not in mgr._cache:
            errors.append(f"Unknown key: {update.key}")
            continue
        pending.append((update.key, update.value))

    if errors:
        raise HTTPException(status_code=400, detail="; ".join(errors))

    try:
        await mgr.set_many(pending)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return mgr.get_all()


class SingleConfigValue(BaseModel):
    """单个配置值"""
    value: Any


@router.put("/{key}")
async def update_single_config(key: str, body: SingleConfigValue = Body(...)):
    """更新单个配置"""
    mgr = ConfigManager.instance()

    if key not in mgr.CONFIG_DEFAULTS and key not in mgr._cache:
        raise HTTPException(status_code=404, detail=f"Unknown config key: {key}")

    try:
        await mgr.set(key, body.value)
        return {"key": key, "value": mgr.get(key)}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/reload")
async def reload_config():
    """强制从数据库重新加载配置"""
    mgr = ConfigManager.instance()
    await mgr.load()
    return {"status": "ok", "count": len(mgr._cache)}


@router.get("/check-connectivity", response_model=ConnectivityResult)
async def check_connectivity():
    """检查 Nintendo API 主机连通性"""
    mgr = ConfigManager.instance()
    config = Config(mgr)

    hosts = mgr.get_json("proxy.hosts", [])
    if not hosts:
        return ConnectivityResult(
            reachable=True, failed_hosts=[], message="无需检查的主机"
        )

    results = await asyncio.gather(*(_check_host(h, config) for h in hosts))
    failed = [h for h, ok in results if not ok]

    if failed:
        msg = "部分主机无法访问，请检查代理配置"
    else:
        msg = "所有主机均可访问"

    return ConnectivityResult(reachable=not failed, failed_hosts=failed, message=msg)
