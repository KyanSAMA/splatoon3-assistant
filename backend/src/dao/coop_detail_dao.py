"""打工详情数据访问层 (DAO)"""

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict, Any

from .connect import get_cursor, get_connection


@dataclass
class CoopDetailData:
    """打工详情数据"""
    user_id: int
    splatoon_id: str                        # 从base64解密的玩家ID (u-xxx)
    played_time: str                        # 游戏时间 (ISO8601)
    rule: str                               # 规则 (REGULAR/BIG_RUN/TEAM_CONTEST)
    danger_rate: Optional[float] = None     # 危险度
    result_wave: Optional[int] = None       # 结果波次 (0=通关)
    smell_meter: Optional[int] = None       # 臭味计
    stage_id: Optional[str] = None          # 场地ID (base64解密后)
    stage_name: Optional[str] = None        # 场地名称
    after_grade_id: Optional[str] = None    # 段位ID (base64解密后)
    after_grade_name: Optional[str] = None  # 段位名称
    after_grade_point: Optional[int] = None # 段位点数
    boss_id: Optional[str] = None           # Extra Wave Boss ID
    boss_name: Optional[str] = None         # Extra Wave Boss 名称
    boss_defeated: int = 0                  # 是否击败Boss (0/1)
    scale_gold: int = 0                     # 金鳞片
    scale_silver: int = 0                   # 银鳞片
    scale_bronze: int = 0                   # 铜鳞片
    job_point: Optional[int] = None         # 打工点数
    job_score: Optional[int] = None         # 打工分数
    job_rate: Optional[float] = None        # 打工倍率
    job_bonus: Optional[int] = None         # 打工奖励
    images: Optional[Dict[str, str]] = None # 图片 {场地名:url, Boss名:url}


@dataclass
class CoopPlayerData:
    """打工玩家数据"""
    coop_id: int                            # 关联 coop_detail.id
    player_order: int                       # 玩家顺序 (0=自己)
    is_myself: int = 0                      # 是否是自己 (0/1)
    player_id: Optional[str] = None         # 玩家ID (base64解密后)
    name: str = ""                          # 玩家名称
    name_id: Optional[str] = None           # 玩家名称ID
    byname: Optional[str] = None            # 称号
    species: Optional[str] = None           # 种族 (INKLING/OCTOLING)
    uniform_id: Optional[str] = None        # 工作服ID (base64解密后)
    uniform_name: Optional[str] = None      # 工作服名称
    special_weapon_id: Optional[int] = None # 大招ID (weaponId字段)
    special_weapon_name: Optional[str] = None # 大招名称
    weapons: Optional[List[str]] = None     # 武器ID列表 (base64解密后)
    weapon_names: Optional[List[str]] = None # 武器名称列表
    defeat_enemy_count: int = 0             # 击杀鲑鱼数
    deliver_count: int = 0                  # 运蛋数(红蛋)
    golden_assist_count: int = 0            # 金蛋助攻数
    golden_deliver_count: int = 0           # 金蛋入筐数
    rescue_count: int = 0                   # 救人次数
    rescued_count: int = 0                  # 被救次数
    images: Optional[Dict[str, str]] = None # 图片 {武器名:url, 大招名:url, 工作服名:url}


@dataclass
class CoopWaveData:
    """打工波次数据"""
    coop_id: int                            # 关联 coop_detail.id
    wave_number: int                        # 波次 (1-4, 4=Extra Wave)
    water_level: Optional[int] = None       # 水位 (0=低, 1=中, 2=高)
    event_id: Optional[str] = None          # 特殊事件ID (base64解密后)
    event_name: Optional[str] = None        # 特殊事件名称
    deliver_norm: Optional[int] = None      # 目标金蛋数
    golden_pop_count: Optional[int] = None  # 金蛋出现数
    team_deliver_count: Optional[int] = None # 团队实际交付数
    special_weapons: Optional[List[str]] = None     # 使用的大招ID列表
    special_weapon_names: Optional[List[str]] = None # 使用的大招名称列表
    images: Optional[Dict[str, str]] = None # 图片 {事件名:url, 大招名:url}


@dataclass
class CoopEnemyData:
    """打工敌人统计数据"""
    coop_id: int                            # 关联 coop_detail.id
    enemy_id: str                           # 敌人ID (base64解密后)
    enemy_name: Optional[str] = None        # 敌人名称
    defeat_count: int = 0                   # 我击杀数
    team_defeat_count: int = 0              # 团队击杀数
    pop_count: int = 0                      # 出现数
    images: Optional[Dict[str, str]] = None # 图片 {敌人名:url}


@dataclass
class CoopBossData:
    """打工Boss结果数据"""
    coop_id: int                            # 关联 coop_detail.id
    boss_id: str                            # Boss ID (base64解密后)
    boss_name: Optional[str] = None         # Boss名称 (横纲/辰龙/巨颚)
    has_defeat_boss: int = 0                # 是否击败 (0/1)
    images: Optional[Dict[str, str]] = None # 图片 {Boss名:url}


# ===========================================
# Coop Detail 操作
# ===========================================

async def get_coop_detail_by_id(coop_id: int) -> Optional[Dict[str, Any]]:
    """根据自增ID获取打工详情"""
    sql = "SELECT * FROM coop_detail WHERE id = ?"
    async with get_cursor(commit=False) as cursor:
        await cursor.execute(sql, (coop_id,))
        return await cursor.fetchone()


async def get_coop_detail_by_played_time(
    user_id: int, splatoon_id: str, played_time: str
) -> Optional[Dict[str, Any]]:
    """根据用户ID、splatoon_id和游玩时间获取打工详情（用于去重）"""
    sql = "SELECT * FROM coop_detail WHERE user_id = ? AND splatoon_id = ? AND played_time = ?"
    async with get_cursor(commit=False) as cursor:
        await cursor.execute(sql, (user_id, splatoon_id, played_time))
        return await cursor.fetchone()


async def get_user_coop_details(
    user_id: int,
    rule: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> List[Dict[str, Any]]:
    """获取用户打工列表"""
    sql = "SELECT * FROM coop_detail WHERE user_id = ?"
    params: List[Any] = [user_id]

    if rule:
        sql += " AND rule = ?"
        params.append(rule)

    sql += " ORDER BY played_time DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    async with get_cursor(commit=False) as cursor:
        await cursor.execute(sql, params)
        return await cursor.fetchall()


async def upsert_coop_detail(data: CoopDetailData) -> int:
    """插入或更新打工详情，返回 coop_detail.id"""
    now = datetime.utcnow().isoformat()
    sql = """
    INSERT INTO coop_detail (
        user_id, splatoon_id, played_time, rule, danger_rate, result_wave,
        smell_meter, stage_id, stage_name, after_grade_id, after_grade_name,
        after_grade_point, boss_id, boss_name, boss_defeated,
        scale_gold, scale_silver, scale_bronze,
        job_point, job_score, job_rate, job_bonus, images, updated_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(user_id, splatoon_id, played_time) DO UPDATE SET
        rule = excluded.rule,
        danger_rate = excluded.danger_rate,
        result_wave = excluded.result_wave,
        smell_meter = excluded.smell_meter,
        stage_id = excluded.stage_id,
        stage_name = excluded.stage_name,
        after_grade_id = excluded.after_grade_id,
        after_grade_name = excluded.after_grade_name,
        after_grade_point = excluded.after_grade_point,
        boss_id = excluded.boss_id,
        boss_name = excluded.boss_name,
        boss_defeated = excluded.boss_defeated,
        scale_gold = excluded.scale_gold,
        scale_silver = excluded.scale_silver,
        scale_bronze = excluded.scale_bronze,
        job_point = excluded.job_point,
        job_score = excluded.job_score,
        job_rate = excluded.job_rate,
        job_bonus = excluded.job_bonus,
        images = excluded.images,
        updated_at = excluded.updated_at
    """
    async with get_cursor() as cursor:
        await cursor.execute(sql, (
            data.user_id, data.splatoon_id, data.played_time, data.rule,
            data.danger_rate, data.result_wave, data.smell_meter,
            data.stage_id, data.stage_name, data.after_grade_id, data.after_grade_name,
            data.after_grade_point, data.boss_id, data.boss_name, data.boss_defeated,
            data.scale_gold, data.scale_silver, data.scale_bronze,
            data.job_point, data.job_score, data.job_rate, data.job_bonus,
            json.dumps(data.images, ensure_ascii=False) if data.images else None,
            now,
        ))
        await cursor.execute(
            "SELECT id FROM coop_detail WHERE user_id = ? AND splatoon_id = ? AND played_time = ?",
            (data.user_id, data.splatoon_id, data.played_time)
        )
        row = await cursor.fetchone()
        return row["id"] if row else 0


# ===========================================
# Coop Player 操作
# ===========================================

async def get_coop_players(coop_id: int) -> List[Dict[str, Any]]:
    """获取打工的所有玩家"""
    sql = "SELECT * FROM coop_player WHERE coop_id = ? ORDER BY player_order"
    async with get_cursor(commit=False) as cursor:
        await cursor.execute(sql, (coop_id,))
        return await cursor.fetchall()


async def batch_upsert_coop_players(records: List[CoopPlayerData]) -> int:
    """批量插入或更新玩家"""
    if not records:
        return 0

    sql = """
    INSERT INTO coop_player (
        coop_id, player_order, is_myself, player_id, name, name_id, byname, species,
        uniform_id, uniform_name, special_weapon_id, special_weapon_name,
        weapons, weapon_names, defeat_enemy_count, deliver_count,
        golden_assist_count, golden_deliver_count, rescue_count, rescued_count, images
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(coop_id, player_order) DO UPDATE SET
        is_myself = excluded.is_myself,
        player_id = excluded.player_id,
        name = excluded.name,
        name_id = excluded.name_id,
        byname = excluded.byname,
        species = excluded.species,
        uniform_id = excluded.uniform_id,
        uniform_name = excluded.uniform_name,
        special_weapon_id = excluded.special_weapon_id,
        special_weapon_name = excluded.special_weapon_name,
        weapons = excluded.weapons,
        weapon_names = excluded.weapon_names,
        defeat_enemy_count = excluded.defeat_enemy_count,
        deliver_count = excluded.deliver_count,
        golden_assist_count = excluded.golden_assist_count,
        golden_deliver_count = excluded.golden_deliver_count,
        rescue_count = excluded.rescue_count,
        rescued_count = excluded.rescued_count,
        images = excluded.images
    """

    async with get_connection() as conn:
        cursor = None
        try:
            cursor = await conn.cursor()
            params = [
                (
                    p.coop_id, p.player_order, p.is_myself, p.player_id, p.name, p.name_id,
                    p.byname, p.species, p.uniform_id, p.uniform_name,
                    p.special_weapon_id, p.special_weapon_name,
                    json.dumps(p.weapons, ensure_ascii=False) if p.weapons else None,
                    json.dumps(p.weapon_names, ensure_ascii=False) if p.weapon_names else None,
                    p.defeat_enemy_count, p.deliver_count, p.golden_assist_count,
                    p.golden_deliver_count, p.rescue_count, p.rescued_count,
                    json.dumps(p.images, ensure_ascii=False) if p.images else None,
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
# Coop Wave 操作
# ===========================================

async def get_coop_waves(coop_id: int) -> List[Dict[str, Any]]:
    """获取打工的所有波次"""
    sql = "SELECT * FROM coop_wave WHERE coop_id = ? ORDER BY wave_number"
    async with get_cursor(commit=False) as cursor:
        await cursor.execute(sql, (coop_id,))
        return await cursor.fetchall()


async def batch_upsert_coop_waves(records: List[CoopWaveData]) -> int:
    """批量插入或更新波次"""
    if not records:
        return 0

    sql = """
    INSERT INTO coop_wave (
        coop_id, wave_number, water_level, event_id, event_name,
        deliver_norm, golden_pop_count, team_deliver_count,
        special_weapons, special_weapon_names, images
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(coop_id, wave_number) DO UPDATE SET
        water_level = excluded.water_level,
        event_id = excluded.event_id,
        event_name = excluded.event_name,
        deliver_norm = excluded.deliver_norm,
        golden_pop_count = excluded.golden_pop_count,
        team_deliver_count = excluded.team_deliver_count,
        special_weapons = excluded.special_weapons,
        special_weapon_names = excluded.special_weapon_names,
        images = excluded.images
    """

    async with get_connection() as conn:
        cursor = None
        try:
            cursor = await conn.cursor()
            params = [
                (
                    w.coop_id, w.wave_number, w.water_level, w.event_id, w.event_name,
                    w.deliver_norm, w.golden_pop_count, w.team_deliver_count,
                    json.dumps(w.special_weapons, ensure_ascii=False) if w.special_weapons else None,
                    json.dumps(w.special_weapon_names, ensure_ascii=False) if w.special_weapon_names else None,
                    json.dumps(w.images, ensure_ascii=False) if w.images else None,
                ) for w in records
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
# Coop Enemy 操作
# ===========================================

async def get_coop_enemies(coop_id: int) -> List[Dict[str, Any]]:
    """获取打工的敌人统计"""
    sql = "SELECT * FROM coop_enemy WHERE coop_id = ?"
    async with get_cursor(commit=False) as cursor:
        await cursor.execute(sql, (coop_id,))
        return await cursor.fetchall()


async def batch_upsert_coop_enemies(records: List[CoopEnemyData]) -> int:
    """批量插入或更新敌人统计"""
    if not records:
        return 0

    sql = """
    INSERT INTO coop_enemy (coop_id, enemy_id, enemy_name, defeat_count, team_defeat_count, pop_count, images)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(coop_id, enemy_id) DO UPDATE SET
        enemy_name = excluded.enemy_name,
        defeat_count = excluded.defeat_count,
        team_defeat_count = excluded.team_defeat_count,
        pop_count = excluded.pop_count,
        images = excluded.images
    """

    async with get_connection() as conn:
        cursor = None
        try:
            cursor = await conn.cursor()
            params = [
                (
                    e.coop_id, e.enemy_id, e.enemy_name,
                    e.defeat_count, e.team_defeat_count, e.pop_count,
                    json.dumps(e.images, ensure_ascii=False) if e.images else None,
                ) for e in records
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
# Coop Boss 操作
# ===========================================

async def get_coop_bosses(coop_id: int) -> List[Dict[str, Any]]:
    """获取打工的Boss结果"""
    sql = "SELECT * FROM coop_boss WHERE coop_id = ?"
    async with get_cursor(commit=False) as cursor:
        await cursor.execute(sql, (coop_id,))
        return await cursor.fetchall()


async def batch_upsert_coop_bosses(records: List[CoopBossData]) -> int:
    """批量插入或更新Boss结果"""
    if not records:
        return 0

    sql = """
    INSERT INTO coop_boss (coop_id, boss_id, boss_name, has_defeat_boss, images)
    VALUES (?, ?, ?, ?, ?)
    ON CONFLICT(coop_id, boss_id) DO UPDATE SET
        boss_name = excluded.boss_name,
        has_defeat_boss = excluded.has_defeat_boss,
        images = excluded.images
    """

    async with get_connection() as conn:
        cursor = None
        try:
            cursor = await conn.cursor()
            params = [
                (
                    b.coop_id, b.boss_id, b.boss_name, b.has_defeat_boss,
                    json.dumps(b.images, ensure_ascii=False) if b.images else None,
                ) for b in records
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
# 删除操作
# ===========================================

async def delete_coop_detail(coop_id: int) -> None:
    """删除打工及关联数据"""
    async with get_connection() as conn:
        cursor = None
        try:
            cursor = await conn.cursor()
            await cursor.execute("DELETE FROM coop_player WHERE coop_id = ?", (coop_id,))
            await cursor.execute("DELETE FROM coop_wave WHERE coop_id = ?", (coop_id,))
            await cursor.execute("DELETE FROM coop_enemy WHERE coop_id = ?", (coop_id,))
            await cursor.execute("DELETE FROM coop_boss WHERE coop_id = ?", (coop_id,))
            await cursor.execute("DELETE FROM coop_detail WHERE id = ?", (coop_id,))
            await conn.commit()
        except Exception:
            await conn.rollback()
            raise
        finally:
            if cursor:
                await cursor.close()
