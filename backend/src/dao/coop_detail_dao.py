"""打工详情数据访问层 (DAO) - SQLAlchemy 2.0"""

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict, Any

from sqlalchemy import select, delete, func
from sqlalchemy.dialects.sqlite import insert

from .database import get_session
from .models.coop import CoopDetail, CoopPlayer, CoopWave, CoopEnemy, CoopBoss


@dataclass
class CoopDetailData:
    """打工详情数据"""
    user_id: int
    splatoon_id: str
    played_time: str
    rule: str
    danger_rate: Optional[float] = None
    result_wave: Optional[int] = None
    smell_meter: Optional[int] = None
    stage_id: Optional[str] = None
    stage_name: Optional[str] = None
    after_grade_id: Optional[str] = None
    after_grade_name: Optional[str] = None
    after_grade_point: Optional[int] = None
    boss_id: Optional[str] = None
    boss_name: Optional[str] = None
    boss_defeated: int = 0
    scale_gold: int = 0
    scale_silver: int = 0
    scale_bronze: int = 0
    job_point: Optional[int] = None
    job_score: Optional[int] = None
    job_rate: Optional[float] = None
    job_bonus: Optional[int] = None
    images: Optional[Dict[str, str]] = None


@dataclass
class CoopPlayerData:
    """打工玩家数据"""
    coop_id: int
    player_order: int
    is_myself: int = 0
    player_id: Optional[str] = None
    name: str = ""
    name_id: Optional[str] = None
    byname: Optional[str] = None
    species: Optional[str] = None
    uniform_id: Optional[str] = None
    uniform_name: Optional[str] = None
    special_weapon_id: Optional[int] = None
    special_weapon_name: Optional[str] = None
    weapons: Optional[List[str]] = None
    weapon_names: Optional[List[str]] = None
    defeat_enemy_count: int = 0
    deliver_count: int = 0
    golden_assist_count: int = 0
    golden_deliver_count: int = 0
    rescue_count: int = 0
    rescued_count: int = 0
    images: Optional[Dict[str, str]] = None


@dataclass
class CoopWaveData:
    """打工波次数据"""
    coop_id: int
    wave_number: int
    water_level: Optional[int] = None
    event_id: Optional[str] = None
    event_name: Optional[str] = None
    deliver_norm: Optional[int] = None
    golden_pop_count: Optional[int] = None
    team_deliver_count: Optional[int] = None
    special_weapons: Optional[List[str]] = None
    special_weapon_names: Optional[List[str]] = None
    images: Optional[Dict[str, str]] = None


@dataclass
class CoopEnemyData:
    """打工敌人统计数据"""
    coop_id: int
    enemy_id: str
    enemy_name: Optional[str] = None
    defeat_count: int = 0
    team_defeat_count: int = 0
    pop_count: int = 0
    images: Optional[Dict[str, str]] = None


@dataclass
class CoopBossData:
    """打工Boss结果数据"""
    coop_id: int
    boss_id: str
    boss_name: Optional[str] = None
    has_defeat_boss: int = 0
    images: Optional[Dict[str, str]] = None


def _json_dumps(data: Any) -> Optional[str]:
    return json.dumps(data, ensure_ascii=False) if data is not None else None


def _apply_coop_filters(stmt, user_id: int, start_time: Optional[str] = None, end_time: Optional[str] = None):
    """复用用户与时间筛选条件"""
    stmt = stmt.where(CoopDetail.user_id == user_id)
    if start_time:
        stmt = stmt.where(CoopDetail.played_time >= start_time)
    if end_time:
        stmt = stmt.where(CoopDetail.played_time <= end_time)
    return stmt


# ===========================================
# Coop Detail 操作
# ===========================================

async def get_coop_detail_by_id(coop_id: int) -> Optional[Dict[str, Any]]:
    """根据自增ID获取打工详情"""
    async with get_session() as session:
        coop = await session.get(CoopDetail, coop_id)
        return coop.to_dict() if coop else None


async def get_coop_detail_by_played_time(
    user_id: int, splatoon_id: str, played_time: str
) -> Optional[Dict[str, Any]]:
    """根据用户ID、splatoon_id和游玩时间获取打工详情（用于去重）"""
    async with get_session() as session:
        stmt = select(CoopDetail).where(
            CoopDetail.user_id == user_id,
            CoopDetail.splatoon_id == splatoon_id,
            CoopDetail.played_time == played_time,
        )
        result = await session.execute(stmt)
        coop = result.scalar_one_or_none()
        return coop.to_dict() if coop else None


async def get_user_coop_details(
    user_id: int,
    rule: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> List[Dict[str, Any]]:
    """获取用户打工列表"""
    async with get_session() as session:
        stmt = select(CoopDetail).where(CoopDetail.user_id == user_id)
        if rule:
            stmt = stmt.where(CoopDetail.rule == rule)
        stmt = stmt.order_by(CoopDetail.played_time.desc()).limit(limit).offset(offset)
        result = await session.execute(stmt)
        coops = result.scalars().all()
        return [c.to_dict() for c in coops]


async def get_filtered_coop_list(
    user_id: int,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
) -> List[Dict[str, Any]]:
    """分页获取打工列表，并附带自己玩家信息"""
    async with get_session() as session:
        coop_id_stmt = select(CoopDetail.id).order_by(CoopDetail.played_time.desc())
        coop_id_stmt = _apply_coop_filters(coop_id_stmt, user_id, start_time, end_time)
        coop_id_stmt = coop_id_stmt.limit(limit).offset(offset)

        coop_id_result = await session.execute(coop_id_stmt)
        coop_ids = [row[0] for row in coop_id_result.fetchall()]
        if not coop_ids:
            return []

        coop_stmt = select(CoopDetail).where(CoopDetail.id.in_(coop_ids))
        coop_result = await session.execute(coop_stmt)
        coop_map = {c.id: c.to_dict() for c in coop_result.scalars().all()}

        player_stmt = (
            select(CoopPlayer)
            .where(CoopPlayer.coop_id.in_(coop_ids), CoopPlayer.is_myself == 1)
        )
        player_result = await session.execute(player_stmt)
        player_map: Dict[int, Dict[str, Any]] = {}
        for player in player_result.scalars().all():
            player_map[player.coop_id] = player.to_dict()

        ordered: List[Dict[str, Any]] = []
        for cid in coop_ids:
            coop_dict = coop_map.get(cid)
            if coop_dict is None:
                continue
            coop_dict["myself"] = player_map.get(cid)
            ordered.append(coop_dict)

        return ordered


async def get_coop_detail_with_relations(coop_id: int, user_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
    """获取完整打工详情，包含玩家/波次/敌人/Boss"""
    async with get_session() as session:
        stmt = select(CoopDetail).where(CoopDetail.id == coop_id)
        if user_id is not None:
            stmt = stmt.where(CoopDetail.user_id == user_id)
        result = await session.execute(stmt)
        coop = result.scalar_one_or_none()
        if not coop:
            return None

        coop_dict = coop.to_dict()

        player_stmt = select(CoopPlayer).where(CoopPlayer.coop_id == coop_id).order_by(CoopPlayer.player_order)
        player_result = await session.execute(player_stmt)
        coop_dict["players"] = [p.to_dict() for p in player_result.scalars().all()]

        wave_stmt = select(CoopWave).where(CoopWave.coop_id == coop_id).order_by(CoopWave.wave_number)
        wave_result = await session.execute(wave_stmt)
        coop_dict["waves"] = [w.to_dict() for w in wave_result.scalars().all()]

        enemy_stmt = select(CoopEnemy).where(CoopEnemy.coop_id == coop_id).order_by(CoopEnemy.id)
        enemy_result = await session.execute(enemy_stmt)
        coop_dict["enemies"] = [e.to_dict() for e in enemy_result.scalars().all()]

        boss_stmt = select(CoopBoss).where(CoopBoss.coop_id == coop_id).order_by(CoopBoss.id)
        boss_result = await session.execute(boss_stmt)
        coop_dict["bosses"] = [b.to_dict() for b in boss_result.scalars().all()]

        return coop_dict


async def upsert_coop_detail(data: CoopDetailData) -> int:
    """插入或更新打工详情，返回 coop_detail.id"""
    now = datetime.utcnow().isoformat()

    async with get_session() as session:
        stmt = insert(CoopDetail).values(
            user_id=data.user_id,
            splatoon_id=data.splatoon_id,
            played_time=data.played_time,
            rule=data.rule,
            danger_rate=data.danger_rate,
            result_wave=data.result_wave,
            smell_meter=data.smell_meter,
            stage_id=data.stage_id,
            stage_name=data.stage_name,
            after_grade_id=data.after_grade_id,
            after_grade_name=data.after_grade_name,
            after_grade_point=data.after_grade_point,
            boss_id=data.boss_id,
            boss_name=data.boss_name,
            boss_defeated=data.boss_defeated,
            scale_gold=data.scale_gold,
            scale_silver=data.scale_silver,
            scale_bronze=data.scale_bronze,
            job_point=data.job_point,
            job_score=data.job_score,
            job_rate=data.job_rate,
            job_bonus=data.job_bonus,
            images=_json_dumps(data.images),
            created_at=now,
            updated_at=now,
        ).on_conflict_do_update(
            index_elements=["user_id", "splatoon_id", "played_time"],
            set_={
                "rule": data.rule,
                "danger_rate": data.danger_rate,
                "result_wave": data.result_wave,
                "smell_meter": data.smell_meter,
                "stage_id": data.stage_id,
                "stage_name": data.stage_name,
                "after_grade_id": data.after_grade_id,
                "after_grade_name": data.after_grade_name,
                "after_grade_point": data.after_grade_point,
                "boss_id": data.boss_id,
                "boss_name": data.boss_name,
                "boss_defeated": data.boss_defeated,
                "scale_gold": data.scale_gold,
                "scale_silver": data.scale_silver,
                "scale_bronze": data.scale_bronze,
                "job_point": data.job_point,
                "job_score": data.job_score,
                "job_rate": data.job_rate,
                "job_bonus": data.job_bonus,
                "images": _json_dumps(data.images),
                "updated_at": now,
            },
        )
        await session.execute(stmt)
        await session.flush()

        query = select(CoopDetail).where(
            CoopDetail.user_id == data.user_id,
            CoopDetail.splatoon_id == data.splatoon_id,
            CoopDetail.played_time == data.played_time,
        )
        result = await session.execute(query)
        coop = result.scalar_one_or_none()
        return coop.id if coop else 0


# ===========================================
# Coop Player 操作
# ===========================================

async def get_coop_players(coop_id: int) -> List[Dict[str, Any]]:
    """获取打工的所有玩家"""
    async with get_session() as session:
        stmt = select(CoopPlayer).where(
            CoopPlayer.coop_id == coop_id
        ).order_by(CoopPlayer.player_order)
        result = await session.execute(stmt)
        players = result.scalars().all()
        return [p.to_dict() for p in players]


async def batch_upsert_coop_players(records: List[CoopPlayerData]) -> int:
    """批量插入或更新玩家"""
    if not records:
        return 0

    now = datetime.utcnow().isoformat()

    async with get_session() as session:
        for p in records:
            stmt = insert(CoopPlayer).values(
                coop_id=p.coop_id,
                player_order=p.player_order,
                is_myself=p.is_myself,
                player_id=p.player_id,
                name=p.name,
                name_id=p.name_id,
                byname=p.byname,
                species=p.species,
                uniform_id=p.uniform_id,
                uniform_name=p.uniform_name,
                special_weapon_id=p.special_weapon_id,
                special_weapon_name=p.special_weapon_name,
                weapons=_json_dumps(p.weapons),
                weapon_names=_json_dumps(p.weapon_names),
                defeat_enemy_count=p.defeat_enemy_count,
                deliver_count=p.deliver_count,
                golden_assist_count=p.golden_assist_count,
                golden_deliver_count=p.golden_deliver_count,
                rescue_count=p.rescue_count,
                rescued_count=p.rescued_count,
                images=_json_dumps(p.images),
                created_at=now,
            ).on_conflict_do_update(
                index_elements=["coop_id", "player_order"],
                set_={
                    "is_myself": p.is_myself,
                    "player_id": p.player_id,
                    "name": p.name,
                    "name_id": p.name_id,
                    "byname": p.byname,
                    "species": p.species,
                    "uniform_id": p.uniform_id,
                    "uniform_name": p.uniform_name,
                    "special_weapon_id": p.special_weapon_id,
                    "special_weapon_name": p.special_weapon_name,
                    "weapons": _json_dumps(p.weapons),
                    "weapon_names": _json_dumps(p.weapon_names),
                    "defeat_enemy_count": p.defeat_enemy_count,
                    "deliver_count": p.deliver_count,
                    "golden_assist_count": p.golden_assist_count,
                    "golden_deliver_count": p.golden_deliver_count,
                    "rescue_count": p.rescue_count,
                    "rescued_count": p.rescued_count,
                    "images": _json_dumps(p.images),
                },
            )
            await session.execute(stmt)

        return len(records)


# ===========================================
# Coop Wave 操作
# ===========================================

async def get_coop_waves(coop_id: int) -> List[Dict[str, Any]]:
    """获取打工的所有波次"""
    async with get_session() as session:
        stmt = select(CoopWave).where(
            CoopWave.coop_id == coop_id
        ).order_by(CoopWave.wave_number)
        result = await session.execute(stmt)
        waves = result.scalars().all()
        return [w.to_dict() for w in waves]


async def batch_upsert_coop_waves(records: List[CoopWaveData]) -> int:
    """批量插入或更新波次"""
    if not records:
        return 0

    now = datetime.utcnow().isoformat()

    async with get_session() as session:
        for w in records:
            stmt = insert(CoopWave).values(
                coop_id=w.coop_id,
                wave_number=w.wave_number,
                water_level=w.water_level,
                event_id=w.event_id,
                event_name=w.event_name,
                deliver_norm=w.deliver_norm,
                golden_pop_count=w.golden_pop_count,
                team_deliver_count=w.team_deliver_count,
                special_weapons=_json_dumps(w.special_weapons),
                special_weapon_names=_json_dumps(w.special_weapon_names),
                images=_json_dumps(w.images),
                created_at=now,
            ).on_conflict_do_update(
                index_elements=["coop_id", "wave_number"],
                set_={
                    "water_level": w.water_level,
                    "event_id": w.event_id,
                    "event_name": w.event_name,
                    "deliver_norm": w.deliver_norm,
                    "golden_pop_count": w.golden_pop_count,
                    "team_deliver_count": w.team_deliver_count,
                    "special_weapons": _json_dumps(w.special_weapons),
                    "special_weapon_names": _json_dumps(w.special_weapon_names),
                    "images": _json_dumps(w.images),
                },
            )
            await session.execute(stmt)

        return len(records)


# ===========================================
# Coop Enemy 操作
# ===========================================

async def get_coop_enemies(coop_id: int) -> List[Dict[str, Any]]:
    """获取打工的敌人统计"""
    async with get_session() as session:
        stmt = select(CoopEnemy).where(CoopEnemy.coop_id == coop_id)
        result = await session.execute(stmt)
        enemies = result.scalars().all()
        return [e.to_dict() for e in enemies]


async def batch_upsert_coop_enemies(records: List[CoopEnemyData]) -> int:
    """批量插入或更新敌人统计"""
    if not records:
        return 0

    now = datetime.utcnow().isoformat()

    async with get_session() as session:
        for e in records:
            stmt = insert(CoopEnemy).values(
                coop_id=e.coop_id,
                enemy_id=e.enemy_id,
                enemy_name=e.enemy_name,
                defeat_count=e.defeat_count,
                team_defeat_count=e.team_defeat_count,
                pop_count=e.pop_count,
                images=_json_dumps(e.images),
                created_at=now,
            ).on_conflict_do_update(
                index_elements=["coop_id", "enemy_id"],
                set_={
                    "enemy_name": e.enemy_name,
                    "defeat_count": e.defeat_count,
                    "team_defeat_count": e.team_defeat_count,
                    "pop_count": e.pop_count,
                    "images": _json_dumps(e.images),
                },
            )
            await session.execute(stmt)

        return len(records)


# ===========================================
# Coop Boss 操作
# ===========================================

async def get_coop_bosses(coop_id: int) -> List[Dict[str, Any]]:
    """获取打工的Boss结果"""
    async with get_session() as session:
        stmt = select(CoopBoss).where(CoopBoss.coop_id == coop_id)
        result = await session.execute(stmt)
        bosses = result.scalars().all()
        return [b.to_dict() for b in bosses]


async def batch_upsert_coop_bosses(records: List[CoopBossData]) -> int:
    """批量插入或更新Boss结果"""
    if not records:
        return 0

    now = datetime.utcnow().isoformat()

    async with get_session() as session:
        for b in records:
            stmt = insert(CoopBoss).values(
                coop_id=b.coop_id,
                boss_id=b.boss_id,
                boss_name=b.boss_name,
                has_defeat_boss=b.has_defeat_boss,
                images=_json_dumps(b.images),
                created_at=now,
            ).on_conflict_do_update(
                index_elements=["coop_id", "boss_id"],
                set_={
                    "boss_name": b.boss_name,
                    "has_defeat_boss": b.has_defeat_boss,
                    "images": _json_dumps(b.images),
                },
            )
            await session.execute(stmt)

        return len(records)


# ===========================================
# 统计查询
# ===========================================

async def get_coop_scale_stats(
    user_id: int,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
) -> Dict[str, int]:
    """统计鳞片累计数量"""
    async with get_session() as session:
        stmt = select(
            func.sum(CoopDetail.scale_gold).label("scale_gold"),
            func.sum(CoopDetail.scale_silver).label("scale_silver"),
            func.sum(CoopDetail.scale_bronze).label("scale_bronze"),
        )
        stmt = _apply_coop_filters(stmt, user_id, start_time, end_time)
        result = await session.execute(stmt)
        row = result.one()
        return {
            "scale_gold": row.scale_gold or 0,
            "scale_silver": row.scale_silver or 0,
            "scale_bronze": row.scale_bronze or 0,
        }


async def get_coop_enemy_stats(
    user_id: int,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """按敌人汇总击破数"""
    async with get_session() as session:
        stmt = (
            select(
                CoopEnemy.enemy_id,
                func.max(CoopEnemy.enemy_name).label("enemy_name"),
                func.sum(CoopEnemy.defeat_count).label("defeat_count"),
            )
            .select_from(CoopEnemy)
            .join(CoopDetail, CoopDetail.id == CoopEnemy.coop_id)
            .group_by(CoopEnemy.enemy_id)
        )
        stmt = _apply_coop_filters(stmt, user_id, start_time, end_time)
        result = await session.execute(stmt)
        return [
            {
                "enemy_id": row.enemy_id,
                "enemy_name": row.enemy_name,
                "defeat_count": row.defeat_count or 0,
            }
            for row in result.fetchall()
        ]


async def get_coop_boss_stats(
    user_id: int,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """按Boss汇总击破次数"""
    async with get_session() as session:
        stmt = (
            select(
                CoopBoss.boss_id,
                func.max(CoopBoss.boss_name).label("boss_name"),
                func.count(CoopBoss.boss_id).label("encounter_count"),
                func.sum(CoopBoss.has_defeat_boss).label("defeat_count"),
            )
            .select_from(CoopBoss)
            .join(CoopDetail, CoopDetail.id == CoopBoss.coop_id)
            .group_by(CoopBoss.boss_id)
        )
        stmt = _apply_coop_filters(stmt, user_id, start_time, end_time)
        result = await session.execute(stmt)
        return [
            {
                "boss_id": row.boss_id,
                "boss_name": row.boss_name,
                "encounter_count": row.encounter_count or 0,
                "defeat_count": row.defeat_count or 0,
            }
            for row in result.fetchall()
        ]


# ===========================================
# 删除操作
# ===========================================

async def delete_coop_detail(coop_id: int) -> None:
    """删除打工及关联数据"""
    async with get_session() as session:
        await session.execute(delete(CoopPlayer).where(CoopPlayer.coop_id == coop_id))
        await session.execute(delete(CoopWave).where(CoopWave.coop_id == coop_id))
        await session.execute(delete(CoopEnemy).where(CoopEnemy.coop_id == coop_id))
        await session.execute(delete(CoopBoss).where(CoopBoss.coop_id == coop_id))
        await session.execute(delete(CoopDetail).where(CoopDetail.id == coop_id))
