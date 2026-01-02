"""打工查询服务 - FastAPI 路由"""

from typing import Optional

from fastapi import APIRouter, Depends, Query

from ..models import User
from ..dao.coop_detail_dao import (
    get_filtered_coop_list,
    get_coop_detail_with_relations,
    get_coop_scale_stats,
    get_coop_enemy_stats,
    get_coop_boss_stats,
)
from .auth_service import require_current_user

router = APIRouter(prefix="/coop", tags=["coop"])


@router.get("/coops")
async def get_coops(
    start_time: Optional[str] = Query(None, description="开始时间 (ISO8601)"),
    end_time: Optional[str] = Query(None, description="结束时间 (ISO8601)"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: User = Depends(require_current_user),
):
    """获取打工列表（附带自己玩家数据）"""
    return await get_filtered_coop_list(
        user_id=user.id,
        start_time=start_time,
        end_time=end_time,
        limit=limit,
        offset=offset,
    )


@router.get("/coops/{coop_id}")
async def get_coop_detail(
    coop_id: int,
    user: User = Depends(require_current_user),
):
    """获取单场打工全量详情"""
    coop = await get_coop_detail_with_relations(coop_id, user_id=user.id)
    if not coop:
        return None
    return coop


@router.get("/stats/scales")
async def get_coop_scales(
    start_time: Optional[str] = Query(None, description="开始时间 (ISO8601)"),
    end_time: Optional[str] = Query(None, description="结束时间 (ISO8601)"),
    user: User = Depends(require_current_user),
):
    """统计鳞片汇总数据"""
    return await get_coop_scale_stats(user_id=user.id, start_time=start_time, end_time=end_time)


@router.get("/stats/enemies")
async def get_coop_enemies(
    start_time: Optional[str] = Query(None, description="开始时间 (ISO8601)"),
    end_time: Optional[str] = Query(None, description="结束时间 (ISO8601)"),
    user: User = Depends(require_current_user),
):
    """统计敌人击破数"""
    return await get_coop_enemy_stats(user_id=user.id, start_time=start_time, end_time=end_time)


@router.get("/stats/bosses")
async def get_coop_bosses(
    start_time: Optional[str] = Query(None, description="开始时间 (ISO8601)"),
    end_time: Optional[str] = Query(None, description="结束时间 (ISO8601)"),
    user: User = Depends(require_current_user),
):
    """统计Boss击破数"""
    return await get_coop_boss_stats(user_id=user.id, start_time=start_time, end_time=end_time)
