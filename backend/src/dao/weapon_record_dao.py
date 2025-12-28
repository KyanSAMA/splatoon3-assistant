"""用户武器战绩数据访问层 (DAO)"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict, Any

from .connect import get_cursor, get_connection


@dataclass
class WeaponRecordData:
    """武器战绩数据"""
    user_id: int
    main_weapon_id: int
    main_weapon_name: str
    last_used_time: Optional[str] = None
    level: int = 0
    exp_to_level_up: int = 0
    win: int = 0
    vibes: float = 0.0
    paint: int = 0
    current_weapon_power: Optional[float] = None
    max_weapon_power: Optional[float] = None


async def get_user_weapon_records(user_id: int) -> List[Dict[str, Any]]:
    """获取用户所有武器战绩"""
    sql = "SELECT * FROM user_weapon_record WHERE user_id = ? ORDER BY main_weapon_id"
    async with get_cursor(commit=False) as cursor:
        await cursor.execute(sql, (user_id,))
        return await cursor.fetchall()


async def get_user_weapon_record(user_id: int, main_weapon_id: int) -> Optional[Dict[str, Any]]:
    """获取用户指定武器的战绩"""
    sql = "SELECT * FROM user_weapon_record WHERE user_id = ? AND main_weapon_id = ?"
    async with get_cursor(commit=False) as cursor:
        await cursor.execute(sql, (user_id, main_weapon_id))
        return await cursor.fetchone()


async def upsert_weapon_record(data: WeaponRecordData) -> Dict[str, Any]:
    """插入或更新武器战绩（以 user_id + main_weapon_id 判重）"""
    now = datetime.utcnow().isoformat()

    sql = """
    INSERT INTO user_weapon_record (
        user_id, main_weapon_id, main_weapon_name, last_used_time,
        level, exp_to_level_up, win, vibes, paint,
        current_weapon_power, max_weapon_power, updated_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(user_id, main_weapon_id) DO UPDATE SET
        main_weapon_name = excluded.main_weapon_name,
        last_used_time = excluded.last_used_time,
        level = excluded.level,
        exp_to_level_up = excluded.exp_to_level_up,
        win = excluded.win,
        vibes = excluded.vibes,
        paint = excluded.paint,
        current_weapon_power = excluded.current_weapon_power,
        max_weapon_power = excluded.max_weapon_power,
        updated_at = excluded.updated_at
    """
    async with get_cursor() as cursor:
        await cursor.execute(sql, (
            data.user_id,
            data.main_weapon_id,
            data.main_weapon_name,
            data.last_used_time,
            data.level,
            data.exp_to_level_up,
            data.win,
            data.vibes,
            data.paint,
            data.current_weapon_power,
            data.max_weapon_power,
            now,
        ))
        await cursor.execute(
            "SELECT * FROM user_weapon_record WHERE user_id = ? AND main_weapon_id = ?",
            (data.user_id, data.main_weapon_id)
        )
        return await cursor.fetchone()


async def batch_upsert_weapon_records(records: List[WeaponRecordData]) -> int:
    """批量插入或更新武器战绩"""
    if not records:
        return 0

    now = datetime.utcnow().isoformat()

    sql = """
    INSERT INTO user_weapon_record (
        user_id, main_weapon_id, main_weapon_name, last_used_time,
        level, exp_to_level_up, win, vibes, paint,
        current_weapon_power, max_weapon_power, updated_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(user_id, main_weapon_id) DO UPDATE SET
        main_weapon_name = excluded.main_weapon_name,
        last_used_time = excluded.last_used_time,
        level = excluded.level,
        exp_to_level_up = excluded.exp_to_level_up,
        win = excluded.win,
        vibes = excluded.vibes,
        paint = excluded.paint,
        current_weapon_power = excluded.current_weapon_power,
        max_weapon_power = excluded.max_weapon_power,
        updated_at = excluded.updated_at
    """

    async with get_connection() as conn:
        cursor = None
        try:
            cursor = await conn.cursor()
            params = [
                (
                    data.user_id,
                    data.main_weapon_id,
                    data.main_weapon_name,
                    data.last_used_time,
                    data.level,
                    data.exp_to_level_up,
                    data.win,
                    data.vibes,
                    data.paint,
                    data.current_weapon_power,
                    data.max_weapon_power,
                    now,
                ) for data in records
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


async def delete_user_weapon_records(user_id: int) -> int:
    """删除用户所有武器战绩"""
    async with get_cursor() as cursor:
        await cursor.execute("DELETE FROM user_weapon_record WHERE user_id = ?", (user_id,))
        return cursor.rowcount