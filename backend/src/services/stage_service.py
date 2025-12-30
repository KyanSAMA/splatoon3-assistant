"""地图服务 - FastAPI 路由"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from ..models import User
from ..dao.stage_stats_dao import (
    get_stages_with_vs_stage_id,
    get_user_stage_stats,
    get_user_stage_best_weapon,
    get_user_all_stage_stats,
    get_user_all_best_weapons,
)
from ..dao.weapon_dao import get_weapon_by_id
from .auth_service import require_current_user

router = APIRouter(prefix="/stage", tags=["stage"])


class StageResponse(BaseModel):
    id: int
    vs_stage_id: int
    code: str
    zh_name: Optional[str] = None
    stage_type: Optional[str] = None


class WinRateResponse(BaseModel):
    AREA: Optional[float] = None
    LOFT: Optional[float] = None
    GOAL: Optional[float] = None
    CLAM: Optional[float] = None
    TURF_WAR: Optional[float] = None


class StageStatsResponse(BaseModel):
    vs_stage_id: int
    win_rate: WinRateResponse


class BestWeaponResponse(BaseModel):
    weapon_id: int
    weapon_name: Optional[str] = None
    vs_rule: str
    win_rate: float
    total_battles: int


class WeaponInfo(BaseModel):
    weapon_id: int
    weapon_code: str
    weapon_name: Optional[str] = None
    win_rate: float
    total_battles: int


class BatchBestWeaponsResponse(BaseModel):
    """批量最佳武器响应，key格式: {vs_stage_id}_{vs_rule}_{mode}"""
    data: dict[str, list[WeaponInfo]]


@router.get("/stages", response_model=list[StageResponse])
async def get_stages():
    """获取所有有 vs_stage_id 的地图"""
    stages = await get_stages_with_vs_stage_id()
    return [
        StageResponse(
            id=s["id"],
            vs_stage_id=s["vs_stage_id"],
            code=s["code"],
            zh_name=s.get("zh_name"),
            stage_type=s.get("stage_type"),
        )
        for s in stages
    ]


@router.get("/stages/{vs_stage_id}/stats", response_model=Optional[StageStatsResponse])
async def get_stage_stats(
    vs_stage_id: int,
    user: User = Depends(require_current_user),
):
    """获取当前用户在指定地图的各模式胜率"""
    stats = await get_user_stage_stats(user.id, vs_stage_id)
    if not stats:
        return None
    return StageStatsResponse(
        vs_stage_id=stats["vs_stage_id"],
        win_rate=WinRateResponse(**stats["win_rate"]),
    )


@router.get("/stages/{vs_stage_id}/best-weapon", response_model=Optional[BestWeaponResponse])
async def get_stage_best_weapon(
    vs_stage_id: int,
    vs_rule: Optional[str] = Query(None, description="规则: AREA/LOFT/GOAL/CLAM/TURF_WAR"),
    min_battles: int = Query(3, ge=1, le=100, description="最少对战场数"),
    user: User = Depends(require_current_user),
):
    """获取当前用户在指定地图的最佳武器"""
    if vs_rule and vs_rule not in ("AREA", "LOFT", "GOAL", "CLAM", "TURF_WAR"):
        raise HTTPException(status_code=400, detail="无效的 vs_rule")

    best = await get_user_stage_best_weapon(user.id, vs_stage_id, vs_rule, min_battles)
    if not best:
        return None

    weapon_name = None
    if best["weapon_id"]:
        weapon = await get_weapon_by_id(best["weapon_id"])
        if weapon:
            weapon_name = weapon.get("weapon_name")

    return BestWeaponResponse(
        weapon_id=best["weapon_id"],
        weapon_name=weapon_name,
        vs_rule=best["vs_rule"],
        win_rate=best["win_rate"],
        total_battles=best["total_battles"],
    )


@router.get("/my-stats", response_model=list[StageStatsResponse])
async def get_my_all_stage_stats(user: User = Depends(require_current_user)):
    """获取当前用户所有地图的胜率统计"""
    stats = await get_user_all_stage_stats(user.id)
    return [
        StageStatsResponse(
            vs_stage_id=s["vs_stage_id"],
            win_rate=WinRateResponse(**s["win_rate"]),
        )
        for s in stats
    ]


@router.get("/my-best-weapons", response_model=BatchBestWeaponsResponse)
async def get_my_all_best_weapons(
    min_battles: int = Query(3, ge=1, le=100, description="最少对战场数"),
    user: User = Depends(require_current_user),
):
    """
    批量获取当前用户所有地图+规则+模式的最佳武器(top 3)

    返回格式: { "data": { "{vs_stage_id}_{vs_rule}_{mode}": [...] } }
    - mode: REGULAR(一般), CHALLENGE(蛮颓挑战), OPEN(蛮颓开放)
    """
    data = await get_user_all_best_weapons(user.id, min_battles)
    return BatchBestWeaponsResponse(data=data)
