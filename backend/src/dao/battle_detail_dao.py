"""对战详情数据访问层 (DAO)"""

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict, Any

from .connect import get_cursor, get_connection


@dataclass
class BattleDetailData:
    """对战详情数据"""
    user_id: int
    splatoon_id: str                        # 从解码ID提取的用户标识
    base64_decode_id: str                   # Base64 解码后的完整 ID
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
    battle_id: int                          # 对应 battle_detail.id
    team_role: str                          # MY/OPPONENT/OTHER
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
    battle_id: int                          # 对应 battle_detail.id
    team_id: int                            # 对应 battle_team.id
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
    head_skills_images: Optional[Dict[str, str]] = None       # {技能名: 图片URL}
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
    battle_id: int                          # 对应 battle_detail.id
    user_id: int
    award_name: str
    award_rank: Optional[str] = None


# ===========================================
# Battle Detail 操作
# ===========================================

async def get_battle_detail_by_id(battle_id: int) -> Optional[Dict[str, Any]]:
    """根据自增ID获取对战详情"""
    sql = "SELECT * FROM battle_detail WHERE id = ?"
    async with get_cursor(commit=False) as cursor:
        await cursor.execute(sql, (battle_id,))
        return await cursor.fetchone()


async def get_battle_detail_by_decode_id(base64_decode_id: str, user_id: int) -> Optional[Dict[str, Any]]:
    """根据解码ID和用户ID获取对战详情（兼容旧接口）"""
    sql = "SELECT * FROM battle_detail WHERE base64_decode_id = ? AND user_id = ?"
    async with get_cursor(commit=False) as cursor:
        await cursor.execute(sql, (base64_decode_id, user_id))
        return await cursor.fetchone()


async def get_battle_detail_by_played_time(
    user_id: int, splatoon_id: str, played_time: str
) -> Optional[Dict[str, Any]]:
    """根据用户ID、splatoon_id和游玩时间获取对战详情（用于去重）"""
    sql = "SELECT * FROM battle_detail WHERE user_id = ? AND splatoon_id = ? AND played_time = ?"
    async with get_cursor(commit=False) as cursor:
        await cursor.execute(sql, (user_id, splatoon_id, played_time))
        return await cursor.fetchone()


async def get_user_battle_details(
    user_id: int,
    vs_mode: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> List[Dict[str, Any]]:
    """获取用户对战列表"""
    sql = "SELECT * FROM battle_detail WHERE user_id = ?"
    params: List[Any] = [user_id]

    if vs_mode:
        sql += " AND vs_mode = ?"
        params.append(vs_mode)

    sql += " ORDER BY played_time DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    async with get_cursor(commit=False) as cursor:
        await cursor.execute(sql, params)
        return await cursor.fetchall()


async def upsert_battle_detail(data: BattleDetailData) -> int:
    """插入或更新对战详情，返回 battle_detail.id"""
    now = datetime.utcnow().isoformat()
    sql = """
    INSERT INTO battle_detail (
        user_id, splatoon_id, base64_decode_id, played_time, duration,
        vs_mode, vs_rule, vs_stage_id, judgement, knockout,
        bankara_mode, udemae, x_power, fest_power,
        league_match_event_id, mode_extra, awards, updated_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(user_id, splatoon_id, played_time) DO UPDATE SET
        base64_decode_id = excluded.base64_decode_id,
        duration = excluded.duration,
        vs_mode = excluded.vs_mode,
        vs_rule = excluded.vs_rule,
        vs_stage_id = excluded.vs_stage_id,
        judgement = excluded.judgement,
        knockout = excluded.knockout,
        bankara_mode = excluded.bankara_mode,
        udemae = excluded.udemae,
        x_power = excluded.x_power,
        fest_power = excluded.fest_power,
        league_match_event_id = excluded.league_match_event_id,
        mode_extra = excluded.mode_extra,
        awards = excluded.awards,
        updated_at = excluded.updated_at
    """
    async with get_cursor() as cursor:
        await cursor.execute(sql, (
            data.user_id,
            data.splatoon_id,
            data.base64_decode_id,
            data.played_time,
            data.duration,
            data.vs_mode,
            data.vs_rule,
            data.vs_stage_id,
            data.judgement,
            data.knockout,
            data.bankara_mode,
            data.udemae,
            data.x_power,
            data.fest_power,
            data.league_match_event_id,
            json.dumps(data.mode_extra, ensure_ascii=False) if data.mode_extra else None,
            json.dumps(data.awards, ensure_ascii=False) if data.awards else None,
            now,
        ))
        # 获取插入/更新后的 ID
        await cursor.execute(
            "SELECT id FROM battle_detail WHERE user_id = ? AND splatoon_id = ? AND played_time = ?",
            (data.user_id, data.splatoon_id, data.played_time)
        )
        row = await cursor.fetchone()
        return row["id"] if row else 0


# ===========================================
# Battle Team 操作
# ===========================================

async def get_battle_teams(battle_id: int) -> List[Dict[str, Any]]:
    """获取对战的所有队伍"""
    sql = "SELECT * FROM battle_team WHERE battle_id = ? ORDER BY team_role, team_order"
    async with get_cursor(commit=False) as cursor:
        await cursor.execute(sql, (battle_id,))
        return await cursor.fetchall()


async def upsert_battle_team(data: BattleTeamData) -> int:
    """插入或更新队伍，返回 team id"""
    sql = """
    INSERT INTO battle_team (
        battle_id, team_role, team_order, paint_ratio, score, noroshi, judgement,
        fest_team_name, fest_uniform_name, fest_uniform_bonus_rate,
        fest_streak_win_count, tricolor_role, color
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(battle_id, team_role, team_order) DO UPDATE SET
        paint_ratio = excluded.paint_ratio,
        score = excluded.score,
        noroshi = excluded.noroshi,
        judgement = excluded.judgement,
        fest_team_name = excluded.fest_team_name,
        fest_uniform_name = excluded.fest_uniform_name,
        fest_uniform_bonus_rate = excluded.fest_uniform_bonus_rate,
        fest_streak_win_count = excluded.fest_streak_win_count,
        tricolor_role = excluded.tricolor_role,
        color = excluded.color
    """
    async with get_cursor() as cursor:
        await cursor.execute(sql, (
            data.battle_id, data.team_role, data.team_order,
            data.paint_ratio, data.score, data.noroshi, data.judgement,
            data.fest_team_name, data.fest_uniform_name, data.fest_uniform_bonus_rate,
            data.fest_streak_win_count, data.tricolor_role,
            json.dumps(data.color, ensure_ascii=False) if data.color else None,
        ))
        await cursor.execute(
            "SELECT id FROM battle_team WHERE battle_id = ? AND team_role = ? AND team_order = ?",
            (data.battle_id, data.team_role, data.team_order)
        )
        row = await cursor.fetchone()
        return row["id"] if row else 0


# ===========================================
# Battle Player 操作
# ===========================================

async def get_battle_players(battle_id: int) -> List[Dict[str, Any]]:
    """获取对战的所有玩家"""
    sql = "SELECT * FROM battle_player WHERE battle_id = ? ORDER BY team_id, player_order"
    async with get_cursor(commit=False) as cursor:
        await cursor.execute(sql, (battle_id,))
        return await cursor.fetchall()


async def batch_upsert_battle_players(records: List[BattlePlayerData]) -> int:
    """批量插入或更新玩家"""
    if not records:
        return 0

    sql = """
    INSERT INTO battle_player (
        battle_id, team_id, player_order, player_id, name, name_id, byname, species,
        is_myself, weapon_id, head_main_skill, head_additional_skills,
        clothing_main_skill, clothing_additional_skills,
        shoes_main_skill, shoes_additional_skills,
        head_skills_images, clothing_skills_images, shoes_skills_images,
        paint, kill_count, assist_count, death_count, special_count, noroshi_try,
        crown, fest_dragon_cert
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(battle_id, team_id, player_order) DO UPDATE SET
        player_id = excluded.player_id,
        name = excluded.name,
        name_id = excluded.name_id,
        byname = excluded.byname,
        species = excluded.species,
        is_myself = excluded.is_myself,
        weapon_id = excluded.weapon_id,
        head_main_skill = excluded.head_main_skill,
        head_additional_skills = excluded.head_additional_skills,
        clothing_main_skill = excluded.clothing_main_skill,
        clothing_additional_skills = excluded.clothing_additional_skills,
        shoes_main_skill = excluded.shoes_main_skill,
        shoes_additional_skills = excluded.shoes_additional_skills,
        head_skills_images = excluded.head_skills_images,
        clothing_skills_images = excluded.clothing_skills_images,
        shoes_skills_images = excluded.shoes_skills_images,
        paint = excluded.paint,
        kill_count = excluded.kill_count,
        assist_count = excluded.assist_count,
        death_count = excluded.death_count,
        special_count = excluded.special_count,
        noroshi_try = excluded.noroshi_try,
        crown = excluded.crown,
        fest_dragon_cert = excluded.fest_dragon_cert
    """

    async with get_connection() as conn:
        cursor = None
        try:
            cursor = await conn.cursor()
            params = [
                (
                    p.battle_id, p.team_id, p.player_order, p.player_id, p.name, p.name_id,
                    p.byname, p.species, p.is_myself, p.weapon_id,
                    p.head_main_skill,
                    json.dumps(p.head_additional_skills, ensure_ascii=False) if p.head_additional_skills else None,
                    p.clothing_main_skill,
                    json.dumps(p.clothing_additional_skills, ensure_ascii=False) if p.clothing_additional_skills else None,
                    p.shoes_main_skill,
                    json.dumps(p.shoes_additional_skills, ensure_ascii=False) if p.shoes_additional_skills else None,
                    json.dumps(p.head_skills_images, ensure_ascii=False) if p.head_skills_images else None,
                    json.dumps(p.clothing_skills_images, ensure_ascii=False) if p.clothing_skills_images else None,
                    json.dumps(p.shoes_skills_images, ensure_ascii=False) if p.shoes_skills_images else None,
                    p.paint, p.kill_count, p.assist_count, p.death_count,
                    p.special_count, p.noroshi_try, p.crown, p.fest_dragon_cert,
                ) for p in records
            ]
            await cursor.executemany(sql, params)
            await conn.commit()
            return len(records)
        except Exception:
            await conn.rollback()
            raise
        finally:
            if cursor:
                await cursor.close()


# ===========================================
# Battle Award 操作
# ===========================================

async def batch_upsert_battle_awards(records: List[BattleAwardData]) -> int:
    """批量插入或更新徽章"""
    if not records:
        return 0

    sql = """
    INSERT INTO battle_award (battle_id, user_id, award_name, award_rank)
    VALUES (?, ?, ?, ?)
    ON CONFLICT(battle_id, award_name) DO UPDATE SET
        award_rank = excluded.award_rank
    """

    async with get_connection() as conn:
        cursor = None
        try:
            cursor = await conn.cursor()
            params = [(a.battle_id, a.user_id, a.award_name, a.award_rank) for a in records]
            await cursor.executemany(sql, params)
            await conn.commit()
            return len(records)
        except Exception:
            await conn.rollback()
            raise
        finally:
            if cursor:
                await cursor.close()


# ===========================================
# 删除操作
# ===========================================

async def delete_battle_detail(battle_id: int) -> None:
    """删除对战及关联数据"""
    async with get_connection() as conn:
        cursor = None
        try:
            cursor = await conn.cursor()
            await cursor.execute("DELETE FROM battle_player WHERE battle_id = ?", (battle_id,))
            await cursor.execute("DELETE FROM battle_team WHERE battle_id = ?", (battle_id,))
            await cursor.execute("DELETE FROM battle_award WHERE battle_id = ?", (battle_id,))
            await cursor.execute("DELETE FROM battle_detail WHERE id = ?", (battle_id,))
            await conn.commit()
        except Exception:
            await conn.rollback()
            raise
        finally:
            if cursor:
                await cursor.close()
