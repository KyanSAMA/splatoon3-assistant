"""对战服务 - FastAPI 路由"""

from typing import Optional, List, Dict, Any

from fastapi import APIRouter, Depends, Query

from ..models import User
from ..dao.battle_detail_dao import (
    get_filtered_battle_list,
    get_battle_detail_by_id,
    get_battle_teams,
    get_battle_players,
    get_battle_stats,
    get_user_used_weapons,
    get_opponent_weapons_on_win,
    get_opponent_weapons_on_lose,
    get_opponent_weapon_win_rates,
    get_opponent_weapon_lose_rates,
    get_teammate_weapon_win_rates,
    get_teammate_weapon_lose_rates,
    get_opponent_weapons_count_on_win,
    get_opponent_weapons_count_on_lose,
)
from ..dao.stage_dao import get_stage_by_vs_stage_id
from ..dao.weapon_dao import get_all_main_weapons, get_all_sub_weapons, get_all_special_weapons
from .auth_service import require_current_user

router = APIRouter(prefix="/battle", tags=["battle"])


@router.get("/battles")
async def get_battles(
    vs_mode: Optional[str] = Query(None, description="模式: REGULAR/BANKARA/X_MATCH/FEST/LEAGUE/PRIVATE"),
    vs_rule: Optional[str] = Query(None, description="规则: TURF_WAR/AREA/LOFT/GOAL/CLAM"),
    weapon_id: Optional[int] = Query(None, description="武器ID"),
    bankara_mode: Optional[str] = Query(None, description="蛮颓模式: OPEN/CHALLENGE"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: User = Depends(require_current_user),
):
    """获取对战列表（包含队伍和玩家）"""
    battles = await get_filtered_battle_list(
        user_id=user.id,
        vs_mode=vs_mode,
        vs_rule=vs_rule,
        weapon_id=weapon_id,
        bankara_mode=bankara_mode,
        limit=limit,
        offset=offset,
    )

    # 批量加载地图信息
    stage_cache: Dict[int, Dict] = {}
    for battle in battles:
        vs_stage_id = battle.get("vs_stage_id")
        if vs_stage_id and vs_stage_id not in stage_cache:
            stage = await get_stage_by_vs_stage_id(vs_stage_id)
            stage_cache[vs_stage_id] = stage
        if vs_stage_id:
            battle["stage"] = stage_cache.get(vs_stage_id)

    return battles


@router.get("/battles/{battle_id}")
async def get_battle_detail(
    battle_id: int,
    user: User = Depends(require_current_user),
):
    """获取对战详情"""
    battle = await get_battle_detail_by_id(battle_id)
    if not battle:
        return None

    # 验证归属
    if battle.get("user_id") != user.id:
        return None

    # 加载队伍和玩家
    teams = await get_battle_teams(battle_id)
    players = await get_battle_players(battle_id)

    # 组装队伍-玩家结构
    team_map = {t["id"]: t for t in teams}
    for t in teams:
        t["players"] = []
    for p in players:
        team = team_map.get(p.get("team_id"))
        if team:
            team["players"].append(p)

    battle["teams"] = teams

    # 加载地图信息
    vs_stage_id = battle.get("vs_stage_id")
    if vs_stage_id:
        stage = await get_stage_by_vs_stage_id(vs_stage_id)
        battle["stage"] = stage

    return battle


@router.get("/stats")
async def get_stats(
    vs_mode: Optional[str] = Query(None),
    vs_rule: Optional[str] = Query(None),
    weapon_id: Optional[int] = Query(None),
    bankara_mode: Optional[str] = Query(None),
    user: User = Depends(require_current_user),
):
    """获取对战统计"""
    stats = await get_battle_stats(
        user_id=user.id,
        vs_mode=vs_mode,
        vs_rule=vs_rule,
        weapon_id=weapon_id,
        bankara_mode=bankara_mode,
    )

    total = stats.get("total", 0)
    win = stats.get("win", 0)
    lose = stats.get("lose", 0)

    return {
        "total": total,
        "win": win,
        "lose": lose,
        "winRate": round((win / total) * 100) if total > 0 else 0,
    }


@router.get("/weapons")
async def get_user_weapons(
    vs_mode: Optional[str] = Query(None),
    vs_rule: Optional[str] = Query(None),
    bankara_mode: Optional[str] = Query(None),
    user: User = Depends(require_current_user),
):
    """获取用户使用过的武器列表"""
    weapons = await get_user_used_weapons(
        user_id=user.id,
        vs_mode=vs_mode,
        vs_rule=vs_rule,
        bankara_mode=bankara_mode,
    )
    return weapons


@router.get("/dashboard")
async def get_dashboard(
    vs_mode: Optional[str] = Query(None),
    vs_rule: Optional[str] = Query(None),
    weapon_id: Optional[int] = Query(None),
    bankara_mode: Optional[str] = Query(None),
    user: User = Depends(require_current_user),
):
    """获取对战仪表盘统计数据"""
    params = {
        "user_id": user.id,
        "vs_mode": vs_mode,
        "vs_rule": vs_rule,
        "weapon_id": weapon_id,
        "bankara_mode": bankara_mode,
    }

    # 基础统计
    stats = await get_battle_stats(**params)
    total = stats.get("total", 0)
    win = stats.get("win", 0)
    lose = stats.get("lose", 0)

    # 对手武器统计
    opponent_win = await get_opponent_weapons_on_win(**params, limit=6)
    opponent_lose = await get_opponent_weapons_on_lose(**params, limit=6)
    opponent_win_total = await get_opponent_weapons_count_on_win(**params)
    opponent_lose_total = await get_opponent_weapons_count_on_lose(**params)

    # 胜率/败率排行
    opponent_win_rates = await get_opponent_weapon_win_rates(**params, limit=5)
    opponent_lose_rates = await get_opponent_weapon_lose_rates(**params, limit=5)

    # 队友统计
    teammate_win_rates = await get_teammate_weapon_win_rates(**params, limit=5)
    teammate_lose_rates = await get_teammate_weapon_lose_rates(**params, limit=5)

    return {
        "stats": {
            "total": total,
            "win": win,
            "lose": lose,
            "winRate": round((win / total) * 100) if total > 0 else 0,
        },
        "opponentStatsWin": opponent_win,
        "opponentStatsLose": opponent_lose,
        "opponentWinTotal": opponent_win_total,
        "opponentLoseTotal": opponent_lose_total,
        "opponentWinRates": [
            {"weapon_id": r["weapon_id"], "win": r["win"], "total": r["total"], "rate": round(r["rate"] * 100)}
            for r in opponent_win_rates
        ],
        "opponentLoseRates": [
            {"weapon_id": r["weapon_id"], "lose": r["lose"], "total": r["total"], "rate": round(r["rate"] * 100)}
            for r in opponent_lose_rates
        ],
        "teammateWinRates": [
            {"weapon_id": r["weapon_id"], "win": r["win"], "total": r["total"], "rate": round(r["rate"] * 100)}
            for r in teammate_win_rates
        ],
        "teammateLoseRates": [
            {"weapon_id": r["weapon_id"], "lose": r["lose"], "total": r["total"], "rate": round(r["rate"] * 100)}
            for r in teammate_lose_rates
        ],
    }


@router.get("/main-weapons")
async def get_main_weapons():
    """获取所有主武器列表（用于前端缓存）"""
    return await get_all_main_weapons()


@router.get("/sub-weapons")
async def get_sub_weapons():
    """获取所有副武器列表（用于前端缓存）"""
    return await get_all_sub_weapons()


@router.get("/special-weapons")
async def get_special_weapons():
    """获取所有特殊武器列表（用于前端缓存）"""
    return await get_all_special_weapons()
