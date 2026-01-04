"""对战详情数据刷新服务"""

import asyncio
import logging
from enum import Enum
from typing import Optional, List, Dict, Any, Tuple

from fastapi import APIRouter, Depends, Query

from ..api.splatnet3_api import SplatNet3API
from ..models import User
from ..utils.id_parser import (
    decode_splatnet_id, extract_vs_stage_id, extract_weapon_id,
    extract_splatoon_id_from_battle, extract_played_time_from_battle_id,
)
from ..dao.battle_detail_dao import (
    BattleDetailData, BattleTeamData, BattlePlayerData, BattleAwardData,
    upsert_battle_detail, upsert_battle_team, batch_upsert_battle_players,
    batch_upsert_battle_awards, get_synced_battle_times,
)
from .auth_service import require_current_user, require_splatnet_api

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/data/refresh", tags=["data"])

MAX_CONCURRENCY = 8


class VsMode(str, Enum):
    """对战模式"""
    REGULAR = "REGULAR"
    BANKARA = "BANKARA"
    X_MATCH = "X_MATCH"
    LEAGUE = "LEAGUE"
    PRIVATE = "PRIVATE"
    FEST = "FEST"
    ALL = "ALL"


# ===========================================
# 数据解析工具
# ===========================================

def _extract_skill_name(gear_power: Optional[Dict]) -> Optional[str]:
    """提取技能名称"""
    if not gear_power:
        return None
    if not isinstance(gear_power, dict):
        logger.warning(f"[DEBUG] gear_power is not dict: type={type(gear_power)}, value={gear_power}")
        return None
    return gear_power.get("name")


def _safe_get_fest_team_name(team: Dict) -> Optional[str]:
    """安全提取祭典队伍名称"""
    fest_team = team.get("festTeamName")
    if not fest_team:
        return None
    if isinstance(fest_team, str):
        return fest_team
    if isinstance(fest_team, dict):
        return fest_team.get("name")
    logger.warning(f"[DEBUG] festTeamName unexpected type: type={type(fest_team)}, value={fest_team}")
    return None


def _extract_additional_skills(gear_powers: Optional[List[Dict]]) -> Optional[List[str]]:
    """提取副技能列表"""
    if not gear_powers:
        return None
    result = []
    for gp in gear_powers:
        if not isinstance(gp, dict):
            logger.warning(f"[DEBUG] gear_power is not dict: type={type(gp)}, value={gp}")
            continue
        if gp.get("name"):
            result.append(gp["name"])
    return result if result else None


def _extract_skill_images(gear: Optional[Dict]) -> Optional[Dict[str, str]]:
    """提取技能图片映射 {技能名: 图片URL}"""
    if not gear:
        return None
    result = {}
    primary = gear.get("primaryGearPower")
    if isinstance(primary, dict) and primary.get("name"):
        image = primary.get("image")
        if isinstance(image, dict) and image.get("url"):
            result[primary["name"]] = image["url"]
    additional = gear.get("additionalGearPowers") or []
    for gp in additional:
        if not isinstance(gp, dict):
            continue
        if gp.get("name"):
            image = gp.get("image")
            if isinstance(image, dict) and image.get("url"):
                result[gp["name"]] = image["url"]
    return result if result else None


def _parse_team_result(result: Optional[Dict]) -> Tuple[Optional[float], Optional[int], Optional[int]]:
    """解析队伍结果：返回 (paint_ratio, score, noroshi)"""
    if not result:
        return (None, None, None)
    if not isinstance(result, dict):
        logger.warning(f"[DEBUG] team result is not dict: type={type(result)}, value={result}")
        return (None, None, None)
    return (
        result.get("paintRatio"),
        result.get("score"),
        result.get("noroshi"),
    )


def _parse_player(
    player: Dict,
    battle_id: int,
    team_id: int,
    player_order: int,
    is_myself: bool = False,
) -> BattlePlayerData:
    """解析玩家数据"""
    # Debug: 检查关键字段类型
    weapon_raw = player.get("weapon")
    if weapon_raw is not None and not isinstance(weapon_raw, dict):
        logger.warning(f"[DEBUG] weapon is not dict: type={type(weapon_raw)}, value={weapon_raw}")
    weapon = weapon_raw if isinstance(weapon_raw, dict) else {}
    weapon_id = extract_weapon_id(weapon.get("id", ""))

    head_gear_raw = player.get("headGear")
    clothing_gear_raw = player.get("clothingGear")
    shoes_gear_raw = player.get("shoesGear")

    if head_gear_raw is not None and not isinstance(head_gear_raw, dict):
        logger.warning(f"[DEBUG] headGear is not dict: type={type(head_gear_raw)}, value={head_gear_raw}")
    if clothing_gear_raw is not None and not isinstance(clothing_gear_raw, dict):
        logger.warning(f"[DEBUG] clothingGear is not dict: type={type(clothing_gear_raw)}, value={clothing_gear_raw}")
    if shoes_gear_raw is not None and not isinstance(shoes_gear_raw, dict):
        logger.warning(f"[DEBUG] shoesGear is not dict: type={type(shoes_gear_raw)}, value={shoes_gear_raw}")

    head_gear = head_gear_raw if isinstance(head_gear_raw, dict) else {}
    clothing_gear = clothing_gear_raw if isinstance(clothing_gear_raw, dict) else {}
    shoes_gear = shoes_gear_raw if isinstance(shoes_gear_raw, dict) else {}

    result = player.get("result") or {}

    return BattlePlayerData(
        battle_id=battle_id,
        team_id=team_id,
        player_order=player_order,
        player_id=decode_splatnet_id(player.get("id", "")) if player.get("id") else None,
        name=player.get("name", ""),
        name_id=player.get("nameId"),
        byname=player.get("byname"),
        species=player.get("species"),
        is_myself=1 if is_myself else 0,
        weapon_id=weapon_id,
        head_main_skill=_extract_skill_name(head_gear.get("primaryGearPower")),
        head_additional_skills=_extract_additional_skills(head_gear.get("additionalGearPowers")),
        clothing_main_skill=_extract_skill_name(clothing_gear.get("primaryGearPower")),
        clothing_additional_skills=_extract_additional_skills(clothing_gear.get("additionalGearPowers")),
        shoes_main_skill=_extract_skill_name(shoes_gear.get("primaryGearPower")),
        shoes_additional_skills=_extract_additional_skills(shoes_gear.get("additionalGearPowers")),
        head_skills_images=_extract_skill_images(head_gear),
        clothing_skills_images=_extract_skill_images(clothing_gear),
        shoes_skills_images=_extract_skill_images(shoes_gear),
        paint=int(result.get("paint") or player.get("paint") or 0),
        kill_count=int(result.get("kill") or 0),
        assist_count=int(result.get("assist") or 0),
        death_count=int(result.get("death") or 0),
        special_count=int(result.get("special") or 0),
        noroshi_try=int(result.get("noroshiTry") or 0),
        crown=1 if player.get("crown") else 0,
        fest_dragon_cert=player.get("festDragonCert"),
    )


async def _parse_and_save_battle_detail(
    user_id: int,
    detail: Dict,
    list_info: Optional[Dict] = None,
) -> Optional[int]:
    """
    解析并保存单条对战详情

    Args:
        user_id: 用户ID
        detail: 对战详情 API 响应
        list_info: 从列表接口获取的额外信息（如 udemae, x_power）

    Returns:
        battle_id (int) 如果成功，None 如果失败
    """
    try:
        vs_detail = (detail.get("data") or {}).get("vsHistoryDetail")
        if not vs_detail:
            return None

        raw_id = vs_detail.get("id", "")
        base64_decode_id = decode_splatnet_id(raw_id)
        splatoon_id = extract_splatoon_id_from_battle(raw_id) or ""

        # Debug: 检查字段类型
        vs_mode_raw = vs_detail.get("vsMode")
        vs_rule_raw = vs_detail.get("vsRule")
        vs_stage_raw = vs_detail.get("vsStage")
        if not isinstance(vs_mode_raw, (dict, type(None))):
            logger.warning(f"[DEBUG] vsMode is not dict: type={type(vs_mode_raw)}, value={vs_mode_raw}")
        if not isinstance(vs_rule_raw, (dict, type(None))):
            logger.warning(f"[DEBUG] vsRule is not dict: type={type(vs_rule_raw)}, value={vs_rule_raw}")
        if not isinstance(vs_stage_raw, (dict, type(None))):
            logger.warning(f"[DEBUG] vsStage is not dict: type={type(vs_stage_raw)}, value={vs_stage_raw}")

        vs_mode = (vs_mode_raw or {}).get("mode", "") if isinstance(vs_mode_raw, dict) else ""
        vs_rule = (vs_rule_raw or {}).get("rule", "") if isinstance(vs_rule_raw, dict) else ""
        vs_stage_id = extract_vs_stage_id((vs_stage_raw or {}).get("id", "")) if isinstance(vs_stage_raw, dict) else None

        # 从列表接口补充的信息
        udemae = (list_info or {}).get("udemae")
        x_power = (list_info or {}).get("x_power")

        # 模式特有信息
        bankara_mode = None
        weapon_power = None
        bankara_power = None
        bankara_match = vs_detail.get("bankaraMatch")
        if isinstance(bankara_match, dict):
            bankara_mode = bankara_match.get("mode")
            weapon_power = bankara_match.get("weaponPower")
            bankara_power_obj = bankara_match.get("bankaraPower")
            if isinstance(bankara_power_obj, dict):
                bankara_power = bankara_power_obj.get("power")
        elif bankara_match:
            logger.warning(f"[DEBUG] bankaraMatch is not dict: type={type(bankara_match)}, value={bankara_match}")

        # 活动赛信息
        my_league_power = None
        league_match_event_name = None
        league_match = vs_detail.get("leagueMatch")
        if isinstance(league_match, dict):
            my_league_power = league_match.get("myLeaguePower")
            league_event = league_match.get("leagueMatchEvent")
            if isinstance(league_event, dict):
                league_match_event_name = league_event.get("name")
        elif league_match:
            logger.warning(f"[DEBUG] leagueMatch is not dict: type={type(league_match)}, value={league_match}")

        # 祭典信息
        fest_power = None
        fest_match = vs_detail.get("festMatch")
        if isinstance(fest_match, dict):
            fest_power = fest_match.get("myFestPower")
        elif fest_match:
            logger.warning(f"[DEBUG] festMatch is not dict: type={type(fest_match)}, value={fest_match}")

        # 徽章
        awards_data = []
        awards_raw = vs_detail.get("awards")
        if isinstance(awards_raw, list):
            for award in awards_raw:
                if isinstance(award, dict):
                    awards_data.append({
                        "name": award.get("name"),
                        "rank": award.get("rank"),
                    })
        elif awards_raw:
            logger.warning(f"[DEBUG] awards is not list: type={type(awards_raw)}, value={awards_raw}")

        # 保存对战主表
        battle_data = BattleDetailData(
            user_id=user_id,
            splatoon_id=splatoon_id,
            base64_decode_id=base64_decode_id,
            played_time=vs_detail.get("playedTime", ""),
            duration=int(vs_detail.get("duration") or 0),
            vs_mode=vs_mode,
            vs_rule=vs_rule,
            vs_stage_id=vs_stage_id,
            judgement=vs_detail.get("judgement", ""),
            knockout=vs_detail.get("knockout"),
            bankara_mode=bankara_mode,
            udemae=udemae,
            x_power=x_power,
            fest_power=fest_power,
            weapon_power=weapon_power,
            bankara_power=bankara_power,
            my_league_power=my_league_power,
            league_match_event_name=league_match_event_name,
            awards=awards_data if awards_data else None,
        )
        battle_id = await upsert_battle_detail(battle_data)
        if not battle_id:
            return None

        # 保存徽章表（便于统计）
        award_records = [
            BattleAwardData(
                battle_id=battle_id,
                user_id=user_id,
                award_name=a["name"],
                award_rank=a.get("rank"),
            ) for a in awards_data if a.get("name")
        ]
        if award_records:
            await batch_upsert_battle_awards(award_records)

        # 保存队伍和玩家
        all_players: List[BattlePlayerData] = []

        # 己方队伍
        my_team = vs_detail.get("myTeam") or {}
        my_team_result = my_team.get("result") or {}
        paint_ratio, score, noroshi = _parse_team_result(my_team_result)

        my_team_data = BattleTeamData(
            battle_id=battle_id,
            team_role="MY",
            team_order=my_team.get("order") or 99,
            paint_ratio=paint_ratio,
            score=score,
            noroshi=noroshi,
            judgement=my_team.get("judgement"),
            color=my_team.get("color"),
            tricolor_role=my_team.get("tricolorRole"),
            fest_team_name=_safe_get_fest_team_name(my_team),
        )
        my_team_id = await upsert_battle_team(my_team_data)
        if not my_team_id:
            logger.error(f"Failed to save my team for battle {battle_id}")
            return None

        # 己方玩家
        my_players = my_team.get("players") or []
        myself_player = vs_detail.get("player") or {}
        myself_id = myself_player.get("id")

        for idx, player in enumerate(my_players):
            is_myself = player.get("id") == myself_id
            all_players.append(_parse_player(player, battle_id, my_team_id, idx, is_myself))

        # 对方队伍
        other_teams = vs_detail.get("otherTeams") or []
        for other_team in other_teams:
            other_result = other_team.get("result") or {}
            o_paint_ratio, o_score, o_noroshi = _parse_team_result(other_result)

            other_team_data = BattleTeamData(
                battle_id=battle_id,
                team_role="OTHER",
                team_order=other_team.get("order") or 99,
                paint_ratio=o_paint_ratio,
                score=o_score,
                noroshi=o_noroshi,
                judgement=other_team.get("judgement"),
                color=other_team.get("color"),
                tricolor_role=other_team.get("tricolorRole"),
                fest_team_name=_safe_get_fest_team_name(other_team),
            )
            other_team_id = await upsert_battle_team(other_team_data)
            if not other_team_id:
                logger.error(f"Failed to save opponent team for battle {battle_id}")
                continue

            # 对方玩家
            other_players = other_team.get("players") or []
            for idx, player in enumerate(other_players):
                all_players.append(_parse_player(player, battle_id, other_team_id, idx))

        # 批量保存玩家
        if all_players:
            await batch_upsert_battle_players(all_players)

        return battle_id

    except Exception as e:
        logger.error(f"Failed to parse battle detail: {e}")
        return None


# ===========================================
# 列表获取与处理
# ===========================================

def _extract_history_nodes(data: Optional[Dict], key: str) -> List[Dict]:
    """从响应中提取 historyDetails.nodes"""
    if not data:
        return []

    histories = (data.get("data") or {}).get(key) or {}
    groups = (histories.get("historyGroups") or {}).get("nodes") or []

    nodes = []
    for group in groups:
        details = (group.get("historyDetails") or {}).get("nodes") or []
        nodes.extend(details)

    return nodes


def _extract_history_groups(data: Optional[Dict], key: str) -> List[Dict]:
    """从响应中提取 historyGroups.nodes（保留分组信息）"""
    if not data:
        return []

    histories = (data.get("data") or {}).get(key) or {}
    return (histories.get("historyGroups") or {}).get("nodes") or []


async def _collect_battle_ids_for_mode(
    api: SplatNet3API,
    mode: VsMode,
) -> Dict[str, str]:
    """收集指定模式的对战 ID -> played_time 映射"""
    id_time_map: Dict[str, str] = {}

    if mode == VsMode.REGULAR:
        data = await api.get_regular_battles()
        nodes = _extract_history_nodes(data, "regularBattleHistories")
    elif mode == VsMode.BANKARA:
        data = await api.get_bankara_battles()
        nodes = _extract_history_nodes(data, "bankaraBattleHistories")
    elif mode == VsMode.X_MATCH:
        data = await api.get_x_battles()
        groups = _extract_history_groups(data, "xBattleHistories")
        nodes = []
        for group in groups:
            group_nodes = (group.get("historyDetails") or {}).get("nodes") or []
            nodes.extend(group_nodes)
    elif mode == VsMode.LEAGUE:
        data = await api.get_event_battles()
        nodes = _extract_history_nodes(data, "eventBattleHistories")
    elif mode == VsMode.PRIVATE:
        data = await api.get_private_battles()
        nodes = _extract_history_nodes(data, "privateBattleHistories")
    else:
        nodes = []

    for node in nodes:
        if not isinstance(node, dict):
            continue
        raw_id = node.get("id", "")
        if not raw_id:
            continue
        played_time = extract_played_time_from_battle_id(raw_id)
        if played_time:
            id_time_map[raw_id] = played_time

    return id_time_map


async def process_battle_by_raw_id(
    api: SplatNet3API,
    user_id: int,
    raw_id: str,
) -> Optional[int]:
    """获取并保存单条对战详情"""
    detail = await api.get_battle_detail(raw_id)
    if not detail:
        return None
    return await _parse_and_save_battle_detail(user_id, detail, {})


# ===========================================
# API 路由
# ===========================================

@router.post("/battle_details")
async def refresh_battle_details(
    mode: Optional[VsMode] = Query(None, description="刷新模式：不传不刷新，传 ALL 刷新所有"),
    user: User = Depends(require_current_user),
    api: SplatNet3API = Depends(require_splatnet_api),
):
    """刷新对战详情数据（预判重 + 并发8）"""
    if mode is None:
        return {"success": True, "message": "No mode specified, skipping refresh", "count": 0}

    modes_to_refresh = []
    if mode == VsMode.ALL:
        modes_to_refresh = [VsMode.REGULAR, VsMode.BANKARA, VsMode.X_MATCH, VsMode.LEAGUE, VsMode.PRIVATE]
    else:
        modes_to_refresh = [mode]

    errors: List[str] = []

    try:
        # 1. 收集所有模式的对战 ID
        all_id_time_map: Dict[str, str] = {}
        for vs_mode in modes_to_refresh:
            try:
                mode_map = await _collect_battle_ids_for_mode(api, vs_mode)
                all_id_time_map.update(mode_map)
                logger.info(f"[Battle:{vs_mode.value}] Found {len(mode_map)} battles")
            except Exception as e:
                logger.error(f"[Battle] Failed to get list for {vs_mode.value}: {e}")
                errors.append(f"{vs_mode.value}: {str(e)}")

        logger.info(f"[Battle] Total found: {len(all_id_time_map)} battles")

        if not all_id_time_map:
            return {"success": True, "message": "No battles found", "count": 0}

        # 2. 预判重：查询已同步的 played_time
        all_times = list(all_id_time_map.values())
        synced_times = await get_synced_battle_times(user.id, all_times)

        # 3. 过滤出需要同步的 ID
        ids_to_sync = [raw_id for raw_id, pt in all_id_time_map.items() if pt not in synced_times]
        logger.info(f"[Battle] Already synced: {len(synced_times)}, need sync: {len(ids_to_sync)}")

        if not ids_to_sync:
            return {"success": True, "message": "All battles already synced", "count": 0}

        # 4. 并发处理（Semaphore 控制并发量为 8）
        semaphore = asyncio.Semaphore(MAX_CONCURRENCY)
        total_saved = 0
        total_failed = 0

        async def fetch_and_save(raw_id: str) -> bool:
            async with semaphore:
                try:
                    saved_id = await process_battle_by_raw_id(api, user.id, raw_id)
                    return saved_id is not None
                except Exception as e:
                    logger.error(f"[Battle] Failed to process {raw_id}: {e}")
                    errors.append(str(e)[:200])
                    return False

        results = await asyncio.gather(*[fetch_and_save(rid) for rid in ids_to_sync])

        for success in results:
            if success:
                total_saved += 1
            else:
                total_failed += 1

    except Exception as e:
        logger.error(f"[Battle] Failed to refresh battle details: {e}")
        errors.append(str(e))
        return {
            "success": False,
            "message": f"Failed to refresh: {str(e)}",
            "count": 0,
            "errors": errors,
        }

    if errors:
        return {
            "success": False,
            "message": f"Refreshed {total_saved} battles with {total_failed} errors",
            "count": total_saved,
            "errors": errors[:10],
        }

    logger.info(f"[Battle] Refreshed {total_saved} battle details for user {user.id}")
    return {"success": True, "message": f"Refreshed {total_saved} battle details", "count": total_saved}


@router.get("/latest_battle_raw")
async def get_latest_battle_raw(
    api: SplatNet3API = Depends(require_splatnet_api),
):
    """
    获取最新一场对战的原始数据（测试用）
    直接返回 SplatNet API 的原始响应
    """
    # 获取最新对战 ID
    last_battle = await api.get_last_one_battle()
    if not last_battle:
        return {"error": "Failed to get last battle info"}

    # 提取对战 ID
    vs_detail = (last_battle.get("data") or {}).get("vsResult") or {}
    history_groups = (vs_detail.get("historyGroups") or {}).get("nodes") or []
    if not history_groups:
        return {"error": "No battle history found", "raw": last_battle}

    first_group = history_groups[0]
    history_details = (first_group.get("historyDetails") or {}).get("nodes") or []
    if not history_details:
        return {"error": "No battle details found", "raw": last_battle}

    battle_id = history_details[0].get("id")
    if not battle_id:
        return {"error": "No battle id found", "raw": last_battle}

    # 获取对战详情
    detail = await api.get_battle_detail(battle_id)
    if not detail:
        return {"error": "Failed to get battle detail", "battle_id": battle_id}

    return detail


@router.get("/recent_battles_raw")
async def get_recent_battles_raw(
        api: SplatNet3API = Depends(require_splatnet_api),
):
    """
    获取最新一场对战的原始数据（测试用）
    直接返回 SplatNet API 的原始响应
    """
    # 获取最新对战 ID
    recent_battles = await api.get_recent_battles()
    return recent_battles
