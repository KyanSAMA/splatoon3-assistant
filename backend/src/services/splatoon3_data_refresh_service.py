"""Splatoon3 数据刷新服务 - FastAPI 路由"""

import logging
from typing import List, Dict, Any

from fastapi import APIRouter, Depends

from ..api.splatnet3_api import SplatNet3API
from ..models import User
from ..dao.stage_record_dao import StageRecordData, batch_upsert_stage_records
from ..dao.stage_dao import get_stages_map_by_vs_stage_id
from ..dao.weapon_record_dao import WeaponRecordData, batch_upsert_weapon_records
from .auth_service import require_current_user, require_splatnet_api

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/data/refresh", tags=["data"])


async def _parse_stage_records(
    user_id: int,
    data: dict,
    stages_map: Dict[int, Dict[str, Any]],
) -> List[StageRecordData]:
    """
    解析 StageRecordQuery 响应数据

    API 响应结构:
    {
        "stats": { "lastPlayedTime": "...", "winRateAr": 0.48, ... },
        "id": "VnNTdGFnZS0x",  // Base64
        "name": "温泉花大峡谷",
        "stageId": 1,          // 对应 stage 表的 id
        "vsStageId": 1         // 对应 stage 表的 vs_stage_id
    }
    """
    records = []
    nodes = data.get("data", {}).get("stageRecords", {}).get("nodes", [])
    for node in nodes:
        try:
            vs_stage_id = node.get("vsStageId")
            if vs_stage_id is None:
                continue

            stats = node.get("stats") or {}

            # 从数据库查找 stage 信息，回填 code 和 id
            stage_info = stages_map.get(vs_stage_id, {})
            stage_id = stage_info.get("id")
            stage_code = stage_info.get("code")

            records.append(StageRecordData(
                user_id=user_id,
                vs_stage_id=vs_stage_id,
                name=node.get("name", ""),
                stage_id=stage_id,
                stage_code=stage_code,
                last_played_time=stats.get("lastPlayedTime"),
                win_rate_ar=stats.get("winRateAr"),
                win_rate_cl=stats.get("winRateCl"),
                win_rate_gl=stats.get("winRateGl"),
                win_rate_lf=stats.get("winRateLf"),
                win_rate_tw=stats.get("winRateTw"),
            ))
        except Exception as e:
            logger.error(f"Failed to parse stage record node: {e}")
    return records


@router.post("/token")
async def refresh_token(
    api: SplatNet3API = Depends(require_splatnet_api),
):
    """
    刷新 Token

    通过调用简单 API 触发 Token 自动刷新机制。
    如果 Token 需要刷新，会花费较长时间（约 5-10 秒）。
    """
    try:
        # 调用简单接口触发 token 刷新
        result = await api.get_last_one_battle()
        if result is None:
            return {"success": False, "message": "API 调用失败", "refreshed": False}
        return {"success": True, "message": "Token 有效", "refreshed": True}
    except Exception as e:
        logger.error(f"Token refresh failed: {e}")
        return {"success": False, "message": str(e), "refreshed": False}


@router.post("/stages_records")
async def refresh_stage_records(
    user: User = Depends(require_current_user),
    api: SplatNet3API = Depends(require_splatnet_api),
):
    """刷新用户地图胜率数据"""
    data = await api.get_stage_records()
    if not data:
        return {"success": False, "message": "Failed to fetch stage records", "count": 0}

    # 预加载 stage 映射表
    stages_map = await get_stages_map_by_vs_stage_id()

    records = await _parse_stage_records(user.id, data, stages_map)
    if not records:
        return {"success": True, "message": "No stage records found", "count": 0}

    count = await batch_upsert_stage_records(records)
    logger.info(f"Refreshed {count} stage records for user {user.id}")
    return {"success": True, "message": f"Refreshed {count} stage records", "count": count}


def _parse_weapon_records(user_id: int, data: dict) -> List[WeaponRecordData]:
    """
    解析 WeaponRecordQuery 响应数据

    API 响应结构:
    {
        "weaponId": 0,
        "name": "广域标记枪",
        "stats": {
            "lastUsedTime": "2024-04-13T08:33:12Z",
            "level": 1,
            "expToLevelUp": 1315,
            "win": 9,
            "vibes": 0.0,
            "paint": 11877,
            "currentWeaponPowerOrder": { "weaponPower": 1750.68, "id": "..." } | null,
            "maxWeaponPower": 1750.68 | null
        }
    }
    """
    records = []
    nodes = (data.get("data") or {}).get("weaponRecords") or {}
    nodes = nodes.get("nodes") or []
    for node in nodes:
        try:
            weapon_id = node.get("weaponId")
            if weapon_id is None:
                continue

            stats = node.get("stats") or {}
            power_order = stats.get("currentWeaponPowerOrder")
            current_power = power_order.get("weaponPower") if power_order else None

            records.append(WeaponRecordData(
                user_id=user_id,
                main_weapon_id=int(weapon_id),
                main_weapon_name=node.get("name") or "",
                last_used_time=stats.get("lastUsedTime"),
                level=int(stats.get("level") or 0),
                exp_to_level_up=int(stats.get("expToLevelUp") or 0),
                win=int(stats.get("win") or 0),
                vibes=float(stats.get("vibes") or 0.0),
                paint=int(stats.get("paint") or 0),
                current_weapon_power=current_power,
                max_weapon_power=stats.get("maxWeaponPower"),
            ))
        except Exception as e:
            logger.error(f"Failed to parse weapon record node: {e}")
    return records


@router.post("/weapon_records")
async def refresh_weapon_records(
    user: User = Depends(require_current_user),
    api: SplatNet3API = Depends(require_splatnet_api),
):
    """刷新用户武器战绩数据"""
    data = await api.get_weapon_records()
    if not data:
        return {"success": False, "message": "Failed to fetch weapon records", "count": 0}

    records = _parse_weapon_records(user.id, data)
    if not records:
        return {"success": True, "message": "No weapon records found", "count": 0}

    count = await batch_upsert_weapon_records(records)
    logger.info(f"Refreshed {count} weapon records for user {user.id}")
    return {"success": True, "message": f"Refreshed {count} weapon records", "count": count}
