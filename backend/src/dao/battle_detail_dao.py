"""对战详情数据访问层 (DAO) - SQLAlchemy 2.0"""

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict, Any

from sqlalchemy import select, delete, func, case, desc, and_, distinct
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
    weapon_power: Optional[float] = None
    bankara_power: Optional[float] = None
    my_league_power: Optional[float] = None
    league_match_event_name: Optional[str] = None
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


# 败场判定常量（包含所有失败类型）
LOSE_JUDGEMENTS = ["LOSE", "DEEMED_LOSE", "EXEMPTED_LOSE"]


def _apply_battle_filters(stmt, user_id: int, vs_mode: Optional[str], vs_rule: Optional[str], bankara_mode: Optional[str] = None):
    """复用用户/模式/规则筛选条件"""
    stmt = stmt.where(BattleDetail.user_id == user_id)
    if vs_mode:
        stmt = stmt.where(BattleDetail.vs_mode == vs_mode)
    if vs_rule:
        stmt = stmt.where(BattleDetail.vs_rule == vs_rule)
    if bankara_mode:
        stmt = stmt.where(BattleDetail.bankara_mode == bankara_mode)
    return stmt


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
            weapon_power=data.weapon_power,
            bankara_power=data.bankara_power,
            my_league_power=data.my_league_power,
            league_match_event_name=data.league_match_event_name,
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
                "weapon_power": data.weapon_power,
                "bankara_power": data.bankara_power,
                "my_league_power": data.my_league_power,
                "league_match_event_name": data.league_match_event_name,
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


# ===========================================
# Battle 统计查询
# ===========================================


async def get_user_used_weapons(
    user_id: int, vs_mode: Optional[str] = None, vs_rule: Optional[str] = None, bankara_mode: Optional[str] = None
) -> List[int]:
    """获取用户自己使用过的武器列表（去重，按 weapon_id 排序）"""
    async with get_session() as session:
        stmt = (
            select(distinct(BattlePlayer.weapon_id))
            .select_from(BattleDetail)
            .join(BattlePlayer, BattlePlayer.battle_id == BattleDetail.id)
            .where(BattlePlayer.is_myself == 1, BattlePlayer.weapon_id.isnot(None))
        )
        stmt = _apply_battle_filters(stmt, user_id, vs_mode, vs_rule, bankara_mode)
        stmt = stmt.order_by(BattlePlayer.weapon_id)
        result = await session.execute(stmt)
        return [row[0] for row in result.fetchall() if row[0] is not None]


async def get_filtered_battle_list(
    user_id: int,
    vs_mode: Optional[str] = None,
    vs_rule: Optional[str] = None,
    weapon_id: Optional[int] = None,
    bankara_mode: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> List[Dict[str, Any]]:
    """
    分页获取对战列表，支持武器筛选
    采用两段查询：先取 battle_id 列表，再批量加载队伍/玩家，避免分页错乱
    """
    async with get_session() as session:
        # 第一段：获取符合条件的 battle_id 列表
        battle_id_stmt = select(BattleDetail.id).order_by(desc(BattleDetail.played_time))
        battle_id_stmt = _apply_battle_filters(battle_id_stmt, user_id, vs_mode, vs_rule, bankara_mode)
        if weapon_id is not None:
            # 通过子查询筛选使用指定武器的对战，添加 user_id 限制提升性能
            weapon_subq = select(BattlePlayer.battle_id).join(
                BattleDetail, BattleDetail.id == BattlePlayer.battle_id
            ).where(
                BattleDetail.user_id == user_id,
                BattlePlayer.is_myself == 1,
                BattlePlayer.weapon_id == weapon_id,
            )
            battle_id_stmt = battle_id_stmt.where(BattleDetail.id.in_(weapon_subq))
        battle_id_stmt = battle_id_stmt.limit(limit).offset(offset)

        battle_id_result = await session.execute(battle_id_stmt)
        battle_ids = [row[0] for row in battle_id_result.fetchall()]
        if not battle_ids:
            return []

        # 第二段：批量加载对战详情
        battle_stmt = select(BattleDetail).where(BattleDetail.id.in_(battle_ids))
        battle_result = await session.execute(battle_stmt)
        battle_map = {b.id: b.to_dict() for b in battle_result.scalars().all()}

        # 批量加载队伍
        team_stmt = (
            select(BattleTeam)
            .where(BattleTeam.battle_id.in_(battle_ids))
            .order_by(BattleTeam.battle_id, BattleTeam.team_role, BattleTeam.team_order)
        )
        team_result = await session.execute(team_stmt)
        teams = team_result.scalars().all()

        # 批量加载玩家
        player_stmt = (
            select(BattlePlayer)
            .where(BattlePlayer.battle_id.in_(battle_ids))
            .order_by(BattlePlayer.battle_id, BattlePlayer.team_id, BattlePlayer.player_order)
        )
        player_result = await session.execute(player_stmt)
        players = player_result.scalars().all()

        # 组装数据结构
        teams_by_battle: Dict[int, List[Dict[str, Any]]] = {bid: [] for bid in battle_ids}
        teams_map: Dict[int, Dict[str, Any]] = {}
        for team in teams:
            team_dict = team.to_dict()
            teams_map[team.id] = team_dict
            teams_by_battle.setdefault(team.battle_id, []).append(team_dict)

        for player in players:
            player_dict = player.to_dict()
            team_dict = teams_map.get(player.team_id)
            if team_dict is not None:
                team_dict.setdefault("players", []).append(player_dict)

        # 按原始顺序返回
        ordered_battles: List[Dict[str, Any]] = []
        for bid in battle_ids:
            battle_dict = battle_map.get(bid)
            if battle_dict is None:
                continue
            battle_dict["teams"] = teams_by_battle.get(bid, [])
            ordered_battles.append(battle_dict)

        return ordered_battles


async def get_battle_stats(
    user_id: int,
    vs_mode: Optional[str] = None,
    vs_rule: Optional[str] = None,
    weapon_id: Optional[int] = None,
    bankara_mode: Optional[str] = None,
) -> Dict[str, int]:
    """获取对战统计：总数/胜场/败场（败场包含 LOSE/DEEMED_LOSE/EXEMPTED_LOSE）"""
    async with get_session() as session:
        stmt = select(
            func.count().label("total"),
            func.sum(case((BattleDetail.judgement == "WIN", 1), else_=0)).label("win"),
            func.sum(case((BattleDetail.judgement.in_(LOSE_JUDGEMENTS), 1), else_=0)).label("lose"),
        )
        stmt = _apply_battle_filters(stmt, user_id, vs_mode, vs_rule, bankara_mode)
        if weapon_id is not None:
            weapon_subq = select(BattlePlayer.battle_id).join(
                BattleDetail, BattleDetail.id == BattlePlayer.battle_id
            ).where(
                BattleDetail.user_id == user_id,
                BattlePlayer.is_myself == 1,
                BattlePlayer.weapon_id == weapon_id,
            )
            stmt = stmt.where(BattleDetail.id.in_(weapon_subq))
        result = await session.execute(stmt)
        row = result.one()
        return {"total": row.total or 0, "win": row.win or 0, "lose": row.lose or 0}


async def get_opponent_weapons_on_win(
    user_id: int,
    vs_mode: Optional[str] = None,
    vs_rule: Optional[str] = None,
    weapon_id: Optional[int] = None,
    bankara_mode: Optional[str] = None,
    limit: int = 6,
) -> List[Dict[str, Any]]:
    """统计获胜对局中对手武器出现次数，按次数降序"""
    async with get_session() as session:
        stmt = (
            select(BattlePlayer.weapon_id, func.count().label("count"))
            .select_from(BattleDetail)
            .join(BattleTeam, BattleTeam.battle_id == BattleDetail.id)
            .join(
                BattlePlayer,
                and_(BattlePlayer.team_id == BattleTeam.id, BattlePlayer.battle_id == BattleDetail.id),
            )
            .where(
                BattleDetail.judgement == "WIN",
                BattleTeam.team_role == "OTHER",
                BattlePlayer.weapon_id.isnot(None),
            )
            .group_by(BattlePlayer.weapon_id)
            .order_by(desc("count"))
            .limit(limit)
        )
        stmt = _apply_battle_filters(stmt, user_id, vs_mode, vs_rule, bankara_mode)
        if weapon_id is not None:
            weapon_subq = select(BattlePlayer.battle_id).join(
                BattleDetail, BattleDetail.id == BattlePlayer.battle_id
            ).where(
                BattleDetail.user_id == user_id,
                BattlePlayer.is_myself == 1,
                BattlePlayer.weapon_id == weapon_id,
            )
            stmt = stmt.where(BattleDetail.id.in_(weapon_subq))
        result = await session.execute(stmt)
        return [{"weapon_id": row.weapon_id, "count": row.count} for row in result.fetchall()]


async def get_opponent_weapons_count_on_win(
    user_id: int,
    vs_mode: Optional[str] = None,
    vs_rule: Optional[str] = None,
    weapon_id: Optional[int] = None,
    bankara_mode: Optional[str] = None,
) -> int:
    """获胜对局中对手武器出现的总次数"""
    async with get_session() as session:
        stmt = (
            select(func.count())
            .select_from(BattleDetail)
            .join(BattleTeam, BattleTeam.battle_id == BattleDetail.id)
            .join(
                BattlePlayer,
                and_(BattlePlayer.team_id == BattleTeam.id, BattlePlayer.battle_id == BattleDetail.id),
            )
            .where(
                BattleDetail.judgement == "WIN",
                BattleTeam.team_role == "OTHER",
                BattlePlayer.weapon_id.isnot(None),
            )
        )
        stmt = _apply_battle_filters(stmt, user_id, vs_mode, vs_rule, bankara_mode)
        if weapon_id is not None:
            weapon_subq = select(BattlePlayer.battle_id).join(
                BattleDetail, BattleDetail.id == BattlePlayer.battle_id
            ).where(
                BattleDetail.user_id == user_id,
                BattlePlayer.is_myself == 1,
                BattlePlayer.weapon_id == weapon_id,
            )
            stmt = stmt.where(BattleDetail.id.in_(weapon_subq))
        result = await session.execute(stmt)
        return result.scalar_one() or 0


async def get_opponent_weapons_on_lose(
    user_id: int,
    vs_mode: Optional[str] = None,
    vs_rule: Optional[str] = None,
    weapon_id: Optional[int] = None,
    bankara_mode: Optional[str] = None,
    limit: int = 6,
) -> List[Dict[str, Any]]:
    """统计失败对局中对手武器出现次数，按次数降序"""
    async with get_session() as session:
        stmt = (
            select(BattlePlayer.weapon_id, func.count().label("count"))
            .select_from(BattleDetail)
            .join(BattleTeam, BattleTeam.battle_id == BattleDetail.id)
            .join(
                BattlePlayer,
                and_(BattlePlayer.team_id == BattleTeam.id, BattlePlayer.battle_id == BattleDetail.id),
            )
            .where(
                BattleDetail.judgement.in_(LOSE_JUDGEMENTS),
                BattleTeam.team_role == "OTHER",
                BattlePlayer.weapon_id.isnot(None),
            )
            .group_by(BattlePlayer.weapon_id)
            .order_by(desc("count"))
            .limit(limit)
        )
        stmt = _apply_battle_filters(stmt, user_id, vs_mode, vs_rule, bankara_mode)
        if weapon_id is not None:
            weapon_subq = select(BattlePlayer.battle_id).join(
                BattleDetail, BattleDetail.id == BattlePlayer.battle_id
            ).where(
                BattleDetail.user_id == user_id,
                BattlePlayer.is_myself == 1,
                BattlePlayer.weapon_id == weapon_id,
            )
            stmt = stmt.where(BattleDetail.id.in_(weapon_subq))
        result = await session.execute(stmt)
        return [{"weapon_id": row.weapon_id, "count": row.count} for row in result.fetchall()]


async def get_opponent_weapons_count_on_lose(
    user_id: int,
    vs_mode: Optional[str] = None,
    vs_rule: Optional[str] = None,
    weapon_id: Optional[int] = None,
    bankara_mode: Optional[str] = None,
) -> int:
    """失败对局中对手武器出现的总次数"""
    async with get_session() as session:
        stmt = (
            select(func.count())
            .select_from(BattleDetail)
            .join(BattleTeam, BattleTeam.battle_id == BattleDetail.id)
            .join(
                BattlePlayer,
                and_(BattlePlayer.team_id == BattleTeam.id, BattlePlayer.battle_id == BattleDetail.id),
            )
            .where(
                BattleDetail.judgement.in_(LOSE_JUDGEMENTS),
                BattleTeam.team_role == "OTHER",
                BattlePlayer.weapon_id.isnot(None),
            )
        )
        stmt = _apply_battle_filters(stmt, user_id, vs_mode, vs_rule, bankara_mode)
        if weapon_id is not None:
            weapon_subq = select(BattlePlayer.battle_id).join(
                BattleDetail, BattleDetail.id == BattlePlayer.battle_id
            ).where(
                BattleDetail.user_id == user_id,
                BattlePlayer.is_myself == 1,
                BattlePlayer.weapon_id == weapon_id,
            )
            stmt = stmt.where(BattleDetail.id.in_(weapon_subq))
        result = await session.execute(stmt)
        return result.scalar_one() or 0


async def get_opponent_weapon_win_rates(
    user_id: int,
    vs_mode: Optional[str] = None,
    vs_rule: Optional[str] = None,
    weapon_id: Optional[int] = None,
    bankara_mode: Optional[str] = None,
    limit: int = 6,
    min_battles: int = 5,
) -> List[Dict[str, Any]]:
    """统计对阵某对手武器时的我方胜率，按胜率降序（按对局去重统计，过滤样本不足的武器）"""
    async with get_session() as session:
        # 按对局去重：使用 distinct(BattleDetail.id) 计数
        stmt = (
            select(
                BattlePlayer.weapon_id.label("weapon_id"),
                # 胜利对局数：只在胜利时返回 battle_id，否则 NULL
                func.count(distinct(case(
                    (BattleDetail.judgement == "WIN", BattleDetail.id), else_=None
                ))).label("win"),
                # 总对局数
                func.count(distinct(BattleDetail.id)).label("total"),
            )
            .select_from(BattleDetail)
            .join(BattleTeam, BattleTeam.battle_id == BattleDetail.id)
            .join(
                BattlePlayer,
                and_(BattlePlayer.team_id == BattleTeam.id, BattlePlayer.battle_id == BattleDetail.id),
            )
            .where(BattleTeam.team_role == "OTHER", BattlePlayer.weapon_id.isnot(None))
            .group_by(BattlePlayer.weapon_id)
        )
        stmt = _apply_battle_filters(stmt, user_id, vs_mode, vs_rule, bankara_mode)
        if weapon_id is not None:
            weapon_subq = select(BattlePlayer.battle_id).join(
                BattleDetail, BattleDetail.id == BattlePlayer.battle_id
            ).where(
                BattleDetail.user_id == user_id,
                BattlePlayer.is_myself == 1,
                BattlePlayer.weapon_id == weapon_id,
            )
            stmt = stmt.where(BattleDetail.id.in_(weapon_subq))
        result = await session.execute(stmt)
        rows = result.fetchall()
        # 在 Python 层计算胜率并排序（避免 SQL 除零），过滤样本不足的武器
        data = [
            {
                "weapon_id": row.weapon_id,
                "win": row.win or 0,
                "total": row.total or 0,
                "rate": (row.win / row.total) if row.total else 0,
            }
            for row in rows
            if (row.total or 0) >= min_battles
        ]
        data.sort(key=lambda x: (-x["rate"], -x["total"]))
        return data[:limit]


async def get_opponent_weapon_lose_rates(
    user_id: int,
    vs_mode: Optional[str] = None,
    vs_rule: Optional[str] = None,
    weapon_id: Optional[int] = None,
    bankara_mode: Optional[str] = None,
    limit: int = 6,
    min_battles: int = 5,
) -> List[Dict[str, Any]]:
    """统计对阵某对手武器时的我方败率，按败率降序（按对局去重统计，过滤样本不足的武器）"""
    async with get_session() as session:
        # 按对局去重统计
        stmt = (
            select(
                BattlePlayer.weapon_id.label("weapon_id"),
                # 失败对局数
                func.count(distinct(case(
                    (BattleDetail.judgement.in_(LOSE_JUDGEMENTS), BattleDetail.id), else_=None
                ))).label("lose"),
                # 总对局数
                func.count(distinct(BattleDetail.id)).label("total"),
            )
            .select_from(BattleDetail)
            .join(BattleTeam, BattleTeam.battle_id == BattleDetail.id)
            .join(
                BattlePlayer,
                and_(BattlePlayer.team_id == BattleTeam.id, BattlePlayer.battle_id == BattleDetail.id),
            )
            .where(BattleTeam.team_role == "OTHER", BattlePlayer.weapon_id.isnot(None))
            .group_by(BattlePlayer.weapon_id)
        )
        stmt = _apply_battle_filters(stmt, user_id, vs_mode, vs_rule, bankara_mode)
        if weapon_id is not None:
            weapon_subq = select(BattlePlayer.battle_id).join(
                BattleDetail, BattleDetail.id == BattlePlayer.battle_id
            ).where(
                BattleDetail.user_id == user_id,
                BattlePlayer.is_myself == 1,
                BattlePlayer.weapon_id == weapon_id,
            )
            stmt = stmt.where(BattleDetail.id.in_(weapon_subq))
        result = await session.execute(stmt)
        rows = result.fetchall()
        data = [
            {
                "weapon_id": row.weapon_id,
                "lose": row.lose or 0,
                "total": row.total or 0,
                "rate": (row.lose / row.total) if row.total else 0,
            }
            for row in rows
            if (row.total or 0) >= min_battles
        ]
        data.sort(key=lambda x: (-x["rate"], -x["total"]))
        return data[:limit]


async def get_teammate_weapon_win_rates(
    user_id: int,
    vs_mode: Optional[str] = None,
    vs_rule: Optional[str] = None,
    weapon_id: Optional[int] = None,
    bankara_mode: Optional[str] = None,
    limit: int = 6,
    min_battles: int = 5,
) -> List[Dict[str, Any]]:
    """统计与某队友武器配合时的胜率（排除自己），按胜率降序（按对局去重统计，过滤样本不足的武器）"""
    async with get_session() as session:
        stmt = (
            select(
                BattlePlayer.weapon_id.label("weapon_id"),
                func.count(distinct(case(
                    (BattleDetail.judgement == "WIN", BattleDetail.id), else_=None
                ))).label("win"),
                func.count(distinct(BattleDetail.id)).label("total"),
            )
            .select_from(BattleDetail)
            .join(BattleTeam, BattleTeam.battle_id == BattleDetail.id)
            .join(
                BattlePlayer,
                and_(BattlePlayer.team_id == BattleTeam.id, BattlePlayer.battle_id == BattleDetail.id),
            )
            .where(
                BattleTeam.team_role == "MY",
                BattlePlayer.is_myself == 0,  # 排除自己
                BattlePlayer.weapon_id.isnot(None),
            )
            .group_by(BattlePlayer.weapon_id)
        )
        stmt = _apply_battle_filters(stmt, user_id, vs_mode, vs_rule, bankara_mode)
        if weapon_id is not None:
            weapon_subq = select(BattlePlayer.battle_id).join(
                BattleDetail, BattleDetail.id == BattlePlayer.battle_id
            ).where(
                BattleDetail.user_id == user_id,
                BattlePlayer.is_myself == 1,
                BattlePlayer.weapon_id == weapon_id,
            )
            stmt = stmt.where(BattleDetail.id.in_(weapon_subq))
        result = await session.execute(stmt)
        rows = result.fetchall()
        data = [
            {
                "weapon_id": row.weapon_id,
                "win": row.win or 0,
                "total": row.total or 0,
                "rate": (row.win / row.total) if row.total else 0,
            }
            for row in rows
            if (row.total or 0) >= min_battles
        ]
        data.sort(key=lambda x: (-x["rate"], -x["total"]))
        return data[:limit]


async def get_teammate_weapon_lose_rates(
    user_id: int,
    vs_mode: Optional[str] = None,
    vs_rule: Optional[str] = None,
    weapon_id: Optional[int] = None,
    bankara_mode: Optional[str] = None,
    limit: int = 6,
    min_battles: int = 5,
) -> List[Dict[str, Any]]:
    """统计与某队友武器配合时的败率（排除自己），按败率降序（按对局去重统计，过滤样本不足的武器）"""
    async with get_session() as session:
        stmt = (
            select(
                BattlePlayer.weapon_id.label("weapon_id"),
                func.count(distinct(case(
                    (BattleDetail.judgement.in_(LOSE_JUDGEMENTS), BattleDetail.id), else_=None
                ))).label("lose"),
                func.count(distinct(BattleDetail.id)).label("total"),
            )
            .select_from(BattleDetail)
            .join(BattleTeam, BattleTeam.battle_id == BattleDetail.id)
            .join(
                BattlePlayer,
                and_(BattlePlayer.team_id == BattleTeam.id, BattlePlayer.battle_id == BattleDetail.id),
            )
            .where(
                BattleTeam.team_role == "MY",
                BattlePlayer.is_myself == 0,  # 排除自己
                BattlePlayer.weapon_id.isnot(None),
            )
            .group_by(BattlePlayer.weapon_id)
        )
        stmt = _apply_battle_filters(stmt, user_id, vs_mode, vs_rule, bankara_mode)
        if weapon_id is not None:
            weapon_subq = select(BattlePlayer.battle_id).join(
                BattleDetail, BattleDetail.id == BattlePlayer.battle_id
            ).where(
                BattleDetail.user_id == user_id,
                BattlePlayer.is_myself == 1,
                BattlePlayer.weapon_id == weapon_id,
            )
            stmt = stmt.where(BattleDetail.id.in_(weapon_subq))
        result = await session.execute(stmt)
        rows = result.fetchall()
        data = [
            {
                "weapon_id": row.weapon_id,
                "lose": row.lose or 0,
                "total": row.total or 0,
                "rate": (row.lose / row.total) if row.total else 0,
            }
            for row in rows
            if (row.total or 0) >= min_battles
        ]
        data.sort(key=lambda x: (-x["rate"], -x["total"]))
        return data[:limit]
