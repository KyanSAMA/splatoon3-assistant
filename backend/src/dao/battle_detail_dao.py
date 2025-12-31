"""对战详情数据访问层 (DAO) - SQLAlchemy 2.0"""

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict, Any

from sqlalchemy import select, delete
from sqlalchemy.dialects.sqlite import insert

from .database import get_session
from .models.battle import BattleDetail, BattleTeam, BattlePlayer, BattleAward


@dataclass
class BattleDetailData:
    """对战详情数据"""
    user_id: int
    splatoon_id: str
    base64_decode_id: str
    played_time: str
    duration: int
    vs_mode: str
    vs_rule: str
    judgement: str
    vs_stage_id: Optional[int] = None
    knockout: Optional[str] = None
    bankara_mode: Optional[str] = None
    udemae: Optional[str] = None
    x_power: Optional[float] = None
    fest_power: Optional[float] = None
    league_match_event_id: Optional[str] = None
    mode_extra: Optional[Dict] = None
    awards: Optional[List[Dict]] = None


@dataclass
class BattleTeamData:
    """队伍数据"""
    battle_id: int
    team_role: str
    team_order: int = 0
    paint_ratio: Optional[float] = None
    score: Optional[int] = None
    noroshi: Optional[int] = None
    judgement: Optional[str] = None
    fest_team_name: Optional[str] = None
    fest_uniform_name: Optional[str] = None
    fest_uniform_bonus_rate: Optional[float] = None
    fest_streak_win_count: Optional[int] = None
    tricolor_role: Optional[str] = None
    color: Optional[Dict] = None


@dataclass
class BattlePlayerData:
    """玩家数据"""
    battle_id: int
    team_id: int
    player_order: int
    name: str
    is_myself: int = 0
    player_id: Optional[str] = None
    name_id: Optional[str] = None
    byname: Optional[str] = None
    species: Optional[str] = None
    weapon_id: Optional[int] = None
    head_main_skill: Optional[str] = None
    head_additional_skills: Optional[List[str]] = None
    clothing_main_skill: Optional[str] = None
    clothing_additional_skills: Optional[List[str]] = None
    shoes_main_skill: Optional[str] = None
    shoes_additional_skills: Optional[List[str]] = None
    head_skills_images: Optional[Dict[str, str]] = None
    clothing_skills_images: Optional[Dict[str, str]] = None
    shoes_skills_images: Optional[Dict[str, str]] = None
    paint: int = 0
    kill_count: int = 0
    assist_count: int = 0
    death_count: int = 0
    special_count: int = 0
    noroshi_try: int = 0
    crown: int = 0
    fest_dragon_cert: Optional[str] = None


@dataclass
class BattleAwardData:
    """徽章数据"""
    battle_id: int
    user_id: int
    award_name: str
    award_rank: Optional[str] = None


def _json_dumps(data: Any) -> Optional[str]:
    return json.dumps(data, ensure_ascii=False) if data is not None else None


# ===========================================
# Battle Detail 操作
# ===========================================

async def get_battle_detail_by_id(battle_id: int) -> Optional[Dict[str, Any]]:
    """根据自增ID获取对战详情"""
    async with get_session() as session:
        battle = await session.get(BattleDetail, battle_id)
        return battle.to_dict() if battle else None


async def get_battle_detail_by_decode_id(base64_decode_id: str, user_id: int) -> Optional[Dict[str, Any]]:
    """根据解码ID和用户ID获取对战详情"""
    async with get_session() as session:
        stmt = select(BattleDetail).where(
            BattleDetail.base64_decode_id == base64_decode_id,
            BattleDetail.user_id == user_id,
        )
        result = await session.execute(stmt)
        battle = result.scalar_one_or_none()
        return battle.to_dict() if battle else None


async def get_battle_detail_by_played_time(
    user_id: int, splatoon_id: str, played_time: str
) -> Optional[Dict[str, Any]]:
    """根据用户ID、splatoon_id和游玩时间获取对战详情（用于去重）"""
    async with get_session() as session:
        stmt = select(BattleDetail).where(
            BattleDetail.user_id == user_id,
            BattleDetail.splatoon_id == splatoon_id,
            BattleDetail.played_time == played_time,
        )
        result = await session.execute(stmt)
        battle = result.scalar_one_or_none()
        return battle.to_dict() if battle else None


async def get_user_battle_details(
    user_id: int,
    vs_mode: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    vs_rule: Optional[str] = None,
    bankara_mode: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """获取用户对战列表"""
    async with get_session() as session:
        stmt = select(BattleDetail).where(BattleDetail.user_id == user_id)
        if vs_mode:
            stmt = stmt.where(BattleDetail.vs_mode == vs_mode)
        if vs_rule:
            stmt = stmt.where(BattleDetail.vs_rule == vs_rule)
        if bankara_mode:
            stmt = stmt.where(BattleDetail.bankara_mode == bankara_mode)
        stmt = stmt.order_by(BattleDetail.played_time.desc()).limit(limit).offset(offset)
        result = await session.execute(stmt)
        battles = result.scalars().all()
        return [b.to_dict() for b in battles]


async def upsert_battle_detail(data: BattleDetailData) -> int:
    """插入或更新对战详情，返回 battle_detail.id"""
    now = datetime.utcnow().isoformat()

    async with get_session() as session:
        stmt = insert(BattleDetail).values(
            user_id=data.user_id,
            splatoon_id=data.splatoon_id,
            base64_decode_id=data.base64_decode_id,
            played_time=data.played_time,
            duration=data.duration,
            vs_mode=data.vs_mode,
            vs_rule=data.vs_rule,
            vs_stage_id=data.vs_stage_id,
            judgement=data.judgement,
            knockout=data.knockout,
            bankara_mode=data.bankara_mode,
            udemae=data.udemae,
            x_power=data.x_power,
            fest_power=data.fest_power,
            league_match_event_id=data.league_match_event_id,
            mode_extra=_json_dumps(data.mode_extra),
            awards=_json_dumps(data.awards),
            created_at=now,
            updated_at=now,
        ).on_conflict_do_update(
            index_elements=["user_id", "splatoon_id", "played_time"],
            set_={
                "base64_decode_id": data.base64_decode_id,
                "duration": data.duration,
                "vs_mode": data.vs_mode,
                "vs_rule": data.vs_rule,
                "vs_stage_id": data.vs_stage_id,
                "judgement": data.judgement,
                "knockout": data.knockout,
                "bankara_mode": data.bankara_mode,
                "udemae": data.udemae,
                "x_power": data.x_power,
                "fest_power": data.fest_power,
                "league_match_event_id": data.league_match_event_id,
                "mode_extra": _json_dumps(data.mode_extra),
                "awards": _json_dumps(data.awards),
                "updated_at": now,
            },
        )
        await session.execute(stmt)
        await session.flush()

        query = select(BattleDetail).where(
            BattleDetail.user_id == data.user_id,
            BattleDetail.splatoon_id == data.splatoon_id,
            BattleDetail.played_time == data.played_time,
        )
        result = await session.execute(query)
        battle = result.scalar_one_or_none()
        return battle.id if battle else 0


# ===========================================
# Battle Team 操作
# ===========================================

async def get_battle_teams(battle_id: int) -> List[Dict[str, Any]]:
    """获取对战的所有队伍"""
    async with get_session() as session:
        stmt = select(BattleTeam).where(
            BattleTeam.battle_id == battle_id
        ).order_by(BattleTeam.team_role, BattleTeam.team_order)
        result = await session.execute(stmt)
        teams = result.scalars().all()
        return [t.to_dict() for t in teams]


async def upsert_battle_team(data: BattleTeamData) -> int:
    """插入或更新队伍，返回 team id"""
    now = datetime.utcnow().isoformat()

    async with get_session() as session:
        stmt = insert(BattleTeam).values(
            battle_id=data.battle_id,
            team_role=data.team_role,
            team_order=data.team_order,
            paint_ratio=data.paint_ratio,
            score=data.score,
            noroshi=data.noroshi,
            judgement=data.judgement,
            fest_team_name=data.fest_team_name,
            fest_uniform_name=data.fest_uniform_name,
            fest_uniform_bonus_rate=data.fest_uniform_bonus_rate,
            fest_streak_win_count=data.fest_streak_win_count,
            tricolor_role=data.tricolor_role,
            color=_json_dumps(data.color),
            created_at=now,
        ).on_conflict_do_update(
            index_elements=["battle_id", "team_role", "team_order"],
            set_={
                "paint_ratio": data.paint_ratio,
                "score": data.score,
                "noroshi": data.noroshi,
                "judgement": data.judgement,
                "fest_team_name": data.fest_team_name,
                "fest_uniform_name": data.fest_uniform_name,
                "fest_uniform_bonus_rate": data.fest_uniform_bonus_rate,
                "fest_streak_win_count": data.fest_streak_win_count,
                "tricolor_role": data.tricolor_role,
                "color": _json_dumps(data.color),
            },
        )
        await session.execute(stmt)
        await session.flush()

        query = select(BattleTeam).where(
            BattleTeam.battle_id == data.battle_id,
            BattleTeam.team_role == data.team_role,
            BattleTeam.team_order == data.team_order,
        )
        result = await session.execute(query)
        team = result.scalar_one_or_none()
        return team.id if team else 0


# ===========================================
# Battle Player 操作
# ===========================================

async def get_battle_players(battle_id: int) -> List[Dict[str, Any]]:
    """获取对战的所有玩家"""
    async with get_session() as session:
        stmt = select(BattlePlayer).where(
            BattlePlayer.battle_id == battle_id
        ).order_by(BattlePlayer.team_id, BattlePlayer.player_order)
        result = await session.execute(stmt)
        players = result.scalars().all()
        return [p.to_dict() for p in players]


async def batch_upsert_battle_players(records: List[BattlePlayerData]) -> int:
    """批量插入或更新玩家"""
    if not records:
        return 0

    now = datetime.utcnow().isoformat()

    async with get_session() as session:
        for p in records:
            stmt = insert(BattlePlayer).values(
                battle_id=p.battle_id,
                team_id=p.team_id,
                player_order=p.player_order,
                player_id=p.player_id,
                name=p.name,
                name_id=p.name_id,
                byname=p.byname,
                species=p.species,
                is_myself=p.is_myself,
                weapon_id=p.weapon_id,
                head_main_skill=p.head_main_skill,
                head_additional_skills=_json_dumps(p.head_additional_skills),
                clothing_main_skill=p.clothing_main_skill,
                clothing_additional_skills=_json_dumps(p.clothing_additional_skills),
                shoes_main_skill=p.shoes_main_skill,
                shoes_additional_skills=_json_dumps(p.shoes_additional_skills),
                head_skills_images=_json_dumps(p.head_skills_images),
                clothing_skills_images=_json_dumps(p.clothing_skills_images),
                shoes_skills_images=_json_dumps(p.shoes_skills_images),
                paint=p.paint,
                kill_count=p.kill_count,
                assist_count=p.assist_count,
                death_count=p.death_count,
                special_count=p.special_count,
                noroshi_try=p.noroshi_try,
                crown=p.crown,
                fest_dragon_cert=p.fest_dragon_cert,
                created_at=now,
            ).on_conflict_do_update(
                index_elements=["battle_id", "team_id", "player_order"],
                set_={
                    "player_id": p.player_id,
                    "name": p.name,
                    "name_id": p.name_id,
                    "byname": p.byname,
                    "species": p.species,
                    "is_myself": p.is_myself,
                    "weapon_id": p.weapon_id,
                    "head_main_skill": p.head_main_skill,
                    "head_additional_skills": _json_dumps(p.head_additional_skills),
                    "clothing_main_skill": p.clothing_main_skill,
                    "clothing_additional_skills": _json_dumps(p.clothing_additional_skills),
                    "shoes_main_skill": p.shoes_main_skill,
                    "shoes_additional_skills": _json_dumps(p.shoes_additional_skills),
                    "head_skills_images": _json_dumps(p.head_skills_images),
                    "clothing_skills_images": _json_dumps(p.clothing_skills_images),
                    "shoes_skills_images": _json_dumps(p.shoes_skills_images),
                    "paint": p.paint,
                    "kill_count": p.kill_count,
                    "assist_count": p.assist_count,
                    "death_count": p.death_count,
                    "special_count": p.special_count,
                    "noroshi_try": p.noroshi_try,
                    "crown": p.crown,
                    "fest_dragon_cert": p.fest_dragon_cert,
                },
            )
            await session.execute(stmt)

        return len(records)


# ===========================================
# Battle Award 操作
# ===========================================

async def batch_upsert_battle_awards(records: List[BattleAwardData]) -> int:
    """批量插入或更新徽章"""
    if not records:
        return 0

    now = datetime.utcnow().isoformat()

    async with get_session() as session:
        for a in records:
            stmt = insert(BattleAward).values(
                battle_id=a.battle_id,
                user_id=a.user_id,
                award_name=a.award_name,
                award_rank=a.award_rank,
                created_at=now,
            ).on_conflict_do_update(
                index_elements=["battle_id", "award_name"],
                set_={"award_rank": a.award_rank},
            )
            await session.execute(stmt)

        return len(records)


# ===========================================
# 删除操作
# ===========================================

async def delete_battle_detail(battle_id: int) -> None:
    """删除对战及关联数据"""
    async with get_session() as session:
        await session.execute(delete(BattlePlayer).where(BattlePlayer.battle_id == battle_id))
        await session.execute(delete(BattleTeam).where(BattleTeam.battle_id == battle_id))
        await session.execute(delete(BattleAward).where(BattleAward.battle_id == battle_id))
        await session.execute(delete(BattleDetail).where(BattleDetail.id == battle_id))
