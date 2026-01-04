"""打工详情数据刷新服务"""

import asyncio
import logging
from typing import Optional, List, Dict

from fastapi import APIRouter, Depends

from ..api.splatnet3_api import SplatNet3API
from ..models import User
from ..utils.id_parser import (
    decode_splatnet_id,
    extract_splatoon_id_from_coop,
    extract_coop_stage_id,
    extract_coop_grade_id,
    extract_coop_enemy_id,
    extract_coop_event_id,
    extract_coop_uniform_id,
    extract_coop_player_id,
    extract_played_time_from_coop_id,
)
from ..dao.coop_detail_dao import (
    CoopDetailData, CoopPlayerData, CoopWaveData, CoopEnemyData, CoopBossData,
    upsert_coop_detail, batch_upsert_coop_players, batch_upsert_coop_waves,
    batch_upsert_coop_enemies, batch_upsert_coop_bosses,
    get_synced_coop_times,
)
from .auth_service import require_current_user, require_splatnet_api

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/data/refresh", tags=["data"])

MAX_CONCURRENCY = 8


# ===========================================
# 数据解析工具
# ===========================================

def _extract_image_url(obj: Optional[Dict]) -> Optional[str]:
    """提取图片URL"""
    if not obj or not isinstance(obj, dict):
        return None
    image = obj.get("image")
    if isinstance(image, dict):
        return image.get("url")
    return None


def _build_images_dict(items: List[tuple]) -> Optional[Dict[str, str]]:
    """构建 {名称: URL} 字典"""
    result = {}
    for name, url in items:
        if name and url:
            result[name] = url
    return result if result else None


def _parse_player(
    player_data: Dict,
    coop_id: int,
    player_order: int,
    is_myself: bool = False,
) -> CoopPlayerData:
    """解析玩家数据"""
    player = player_data.get("player") or {}

    uniform = player.get("uniform") or {}
    uniform_id = extract_coop_uniform_id(uniform.get("id", "")) if uniform.get("id") else None
    uniform_name = uniform.get("name")

    special = player_data.get("specialWeapon") or {}
    special_weapon_id = special.get("weaponId")
    special_weapon_name = special.get("name")

    weapons_raw = player_data.get("weapons") or []
    weapon_names = []
    weapon_images = []
    for w in weapons_raw:
        if not isinstance(w, dict):
            continue
        weapon_names.append(w.get("name"))
        weapon_images.append((w.get("name"), _extract_image_url(w)))

    images_items = weapon_images.copy()
    if special_weapon_name:
        images_items.append((special_weapon_name, _extract_image_url(special)))
    if uniform_name:
        images_items.append((uniform_name, _extract_image_url(uniform)))

    return CoopPlayerData(
        coop_id=coop_id,
        player_order=player_order,
        is_myself=1 if is_myself else 0,
        player_id=extract_coop_player_id(player.get("id", "")) if player.get("id") else None,
        name=player.get("name", ""),
        name_id=player.get("nameId"),
        byname=player.get("byname"),
        species=player.get("species"),
        uniform_id=uniform_id,
        uniform_name=uniform_name,
        special_weapon_id=special_weapon_id,
        special_weapon_name=special_weapon_name,
        weapons=None,
        weapon_names=[n for n in weapon_names if n] if weapon_names else None,
        defeat_enemy_count=int(player_data.get("defeatEnemyCount") or 0),
        deliver_count=int(player_data.get("deliverCount") or 0),
        golden_assist_count=int(player_data.get("goldenAssistCount") or 0),
        golden_deliver_count=int(player_data.get("goldenDeliverCount") or 0),
        rescue_count=int(player_data.get("rescueCount") or 0),
        rescued_count=int(player_data.get("rescuedCount") or 0),
        images=_build_images_dict(images_items),
    )


def _parse_wave(wave_data: Dict, coop_id: int) -> CoopWaveData:
    """解析波次数据"""
    event = wave_data.get("eventWave") or {}
    event_id = extract_coop_event_id(event.get("id", "")) if event.get("id") else None
    event_name = event.get("name")

    specials_raw = wave_data.get("specialWeapons") or []
    special_ids = []
    special_names = []
    special_images = []
    for s in specials_raw:
        if isinstance(s, dict):
            s_id = s.get("id")
            s_name = s.get("name")
            if s_id:
                special_ids.append(decode_splatnet_id(s_id))
            if s_name:
                special_names.append(s_name)
            special_images.append((s_name, _extract_image_url(s)))

    images_items = special_images.copy()
    if event_name:
        images_items.append((event_name, _extract_image_url(event)))

    return CoopWaveData(
        coop_id=coop_id,
        wave_number=int(wave_data.get("waveNumber") or 0),
        water_level=wave_data.get("waterLevel"),
        event_id=event_id,
        event_name=event_name,
        deliver_norm=wave_data.get("deliverNorm"),
        golden_pop_count=wave_data.get("goldenPopCount"),
        team_deliver_count=wave_data.get("teamDeliverCount"),
        special_weapons=special_ids if special_ids else None,
        special_weapon_names=special_names if special_names else None,
        images=_build_images_dict(images_items),
    )


def _parse_enemy(enemy_data: Dict, coop_id: int) -> CoopEnemyData:
    """解析敌人统计数据"""
    enemy = enemy_data.get("enemy") or {}
    enemy_id = extract_coop_enemy_id(enemy.get("id", "")) if enemy.get("id") else ""
    enemy_name = enemy.get("name")

    images_items = []
    if enemy_name:
        images_items.append((enemy_name, _extract_image_url(enemy)))

    return CoopEnemyData(
        coop_id=coop_id,
        enemy_id=enemy_id,
        enemy_name=enemy_name,
        defeat_count=int(enemy_data.get("defeatCount") or 0),
        team_defeat_count=int(enemy_data.get("teamDefeatCount") or 0),
        pop_count=int(enemy_data.get("popCount") or 0),
        images=_build_images_dict(images_items),
    )


def _parse_boss(boss_data: Dict, coop_id: int) -> CoopBossData:
    """解析Boss结果数据"""
    boss = boss_data.get("boss") or {}
    boss_id = extract_coop_enemy_id(boss.get("id", "")) if boss.get("id") else ""
    boss_name = boss.get("name")

    images_items = []
    if boss_name:
        images_items.append((boss_name, _extract_image_url(boss)))

    return CoopBossData(
        coop_id=coop_id,
        boss_id=boss_id,
        boss_name=boss_name,
        has_defeat_boss=1 if boss_data.get("hasDefeatBoss") else 0,
        images=_build_images_dict(images_items),
    )


async def _parse_and_save_coop_detail(
    user_id: int,
    detail: Dict,
) -> Optional[int]:
    """解析并保存单条打工详情"""
    try:
        coop_detail = (detail.get("data") or {}).get("coopHistoryDetail")
        if not coop_detail:
            return None

        raw_id = coop_detail.get("id", "")
        splatoon_id = extract_splatoon_id_from_coop(raw_id) or ""
        played_time = coop_detail.get("playedTime", "")

        stage = coop_detail.get("coopStage") or {}
        stage_id = extract_coop_stage_id(stage.get("id", "")) if stage.get("id") else None
        stage_name = stage.get("name")

        after_grade = coop_detail.get("afterGrade") or {}
        after_grade_id = extract_coop_grade_id(after_grade.get("id", "")) if after_grade.get("id") else None
        after_grade_name = after_grade.get("name")

        boss_result = coop_detail.get("bossResult") or {}
        boss = boss_result.get("boss") or {}
        boss_id = extract_coop_enemy_id(boss.get("id", "")) if boss.get("id") else None
        boss_name = boss.get("name")
        boss_defeated = 1 if boss_result.get("hasDefeatBoss") else 0

        scale = coop_detail.get("scale") or {}

        images_items = []
        if stage_name:
            images_items.append((stage_name, _extract_image_url(stage)))
        if boss_name:
            images_items.append((boss_name, _extract_image_url(boss)))

        coop_data = CoopDetailData(
            user_id=user_id,
            splatoon_id=splatoon_id,
            played_time=played_time,
            rule=coop_detail.get("rule", ""),
            danger_rate=coop_detail.get("dangerRate"),
            result_wave=coop_detail.get("resultWave"),
            smell_meter=coop_detail.get("smellMeter"),
            stage_id=stage_id,
            stage_name=stage_name,
            after_grade_id=after_grade_id,
            after_grade_name=after_grade_name,
            after_grade_point=coop_detail.get("afterGradePoint"),
            boss_id=boss_id,
            boss_name=boss_name,
            boss_defeated=boss_defeated,
            scale_gold=int(scale.get("gold") or 0),
            scale_silver=int(scale.get("silver") or 0),
            scale_bronze=int(scale.get("bronze") or 0),
            job_point=coop_detail.get("jobPoint"),
            job_score=coop_detail.get("jobScore"),
            job_rate=coop_detail.get("jobRate"),
            job_bonus=coop_detail.get("jobBonus"),
            images=_build_images_dict(images_items),
        )
        coop_id = await upsert_coop_detail(coop_data)
        if not coop_id:
            return None

        players: List[CoopPlayerData] = []
        my_result = coop_detail.get("myResult")
        if isinstance(my_result, dict):
            players.append(_parse_player(my_result, coop_id, 0, is_myself=True))

        member_results = coop_detail.get("memberResults") or []
        for idx, member in enumerate(member_results):
            if not isinstance(member, dict):
                continue
            players.append(_parse_player(member, coop_id, idx + 1, is_myself=False))

        if players:
            await batch_upsert_coop_players(players)

        waves: List[CoopWaveData] = []
        wave_results = coop_detail.get("waveResults") or []
        for wave_data in wave_results:
            if not isinstance(wave_data, dict):
                continue
            waves.append(_parse_wave(wave_data, coop_id))

        if waves:
            await batch_upsert_coop_waves(waves)

        enemies: List[CoopEnemyData] = []
        enemy_results = coop_detail.get("enemyResults") or []
        for enemy_data in enemy_results:
            if not isinstance(enemy_data, dict):
                continue
            enemies.append(_parse_enemy(enemy_data, coop_id))

        if enemies:
            await batch_upsert_coop_enemies(enemies)

        bosses: List[CoopBossData] = []
        boss_results = coop_detail.get("bossResults") or []
        for boss_data in boss_results:
            if not isinstance(boss_data, dict):
                continue
            bosses.append(_parse_boss(boss_data, coop_id))

        if bosses:
            await batch_upsert_coop_bosses(bosses)

        return coop_id

    except Exception as e:
        logger.error(f"Failed to parse coop detail: {e}")
        return None


# ===========================================
# API 路由
# ===========================================

@router.post("/coop_details")
async def refresh_coop_details(
    user: User = Depends(require_current_user),
    api: SplatNet3API = Depends(require_splatnet_api),
):
    """刷新打工详情数据（预判重 + 并发8）"""
    errors: List[str] = []

    try:
        # 1. 获取打工列表
        coop_list = await api.get_coops()
        groups = ((coop_list or {}).get("data") or {}).get("coopResult", {}).get("historyGroups", {}).get("nodes") or []

        # 2. 提取所有 raw_id 和 played_time
        id_time_map: Dict[str, str] = {}
        for group in groups:
            if not isinstance(group, dict):
                continue
            nodes = (group.get("historyDetails") or {}).get("nodes") or []
            for node in nodes:
                if not isinstance(node, dict):
                    continue
                raw_id = node.get("id", "")
                if not raw_id:
                    continue
                played_time = extract_played_time_from_coop_id(raw_id)
                if played_time:
                    id_time_map[raw_id] = played_time

        logger.info(f"[Coop] Found {len(id_time_map)} coop battles for user {user.id}")

        if not id_time_map:
            return {"success": True, "message": "No coop battles found", "count": 0}

        # 3. 预判重
        all_times = list(id_time_map.values())
        synced_times = await get_synced_coop_times(user.id, all_times)

        # 4. 过滤出需要同步的 ID
        ids_to_sync = [raw_id for raw_id, pt in id_time_map.items() if pt not in synced_times]
        logger.info(f"[Coop] Already synced: {len(synced_times)}, need sync: {len(ids_to_sync)}")

        if not ids_to_sync:
            return {"success": True, "message": "All coop battles already synced", "count": 0}

        # 5. 并发处理（Semaphore 控制并发量为 8）
        semaphore = asyncio.Semaphore(MAX_CONCURRENCY)
        total_saved = 0
        total_failed = 0

        async def fetch_and_save(raw_id: str) -> bool:
            async with semaphore:
                try:
                    detail = await api.get_coop_detail(raw_id)
                    if not detail:
                        return False
                    saved_id = await _parse_and_save_coop_detail(user.id, detail)
                    return saved_id is not None
                except Exception as e:
                    logger.error(f"[Coop] Failed to process {raw_id}: {e}")
                    errors.append(str(e)[:200])
                    return False

        results = await asyncio.gather(*[fetch_and_save(rid) for rid in ids_to_sync])

        for success in results:
            if success:
                total_saved += 1
            else:
                total_failed += 1

    except Exception as e:
        logger.error(f"[Coop] Failed to refresh: {e}")
        errors.append(str(e))
        return {"success": False, "message": f"Failed: {str(e)}", "count": 0, "errors": errors}

    if errors:
        return {
            "success": False,
            "message": f"Refreshed {total_saved} coop details with {total_failed} errors",
            "count": total_saved,
            "errors": errors[:10],
        }

    logger.info(f"[Coop] Refreshed {total_saved} coop details for user {user.id}")
    return {"success": True, "message": f"Refreshed {total_saved} coop details", "count": total_saved}


@router.get("/coops_raw")
async def get_coops_raw(
        api: SplatNet3API = Depends(require_splatnet_api),
):
    """获取打工列表原始数据（测试用）"""
    coops = await api.get_coops()
    return coops
