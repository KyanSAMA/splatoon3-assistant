"""用户地图胜率数据访问层 (DAO)"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict, Any

from .connect import get_cursor, get_connection


@dataclass
class StageRecordData:
    """地图胜率数据"""
    user_id: int
    vs_stage_id: int
    name: str
    stage_id: Optional[int] = None
    stage_code: Optional[str] = None
    last_played_time: Optional[str] = None
    win_rate_ar: Optional[float] = None
    win_rate_cl: Optional[float] = None
    win_rate_gl: Optional[float] = None
    win_rate_lf: Optional[float] = None
    win_rate_tw: Optional[float] = None


async def get_user_stage_records(user_id: int) -> List[Dict[str, Any]]:
    """获取用户所有地图胜率记录"""
    sql = "SELECT * FROM user_stage_record WHERE user_id = ? ORDER BY vs_stage_id"
    async with get_cursor(commit=False) as cursor:
        await cursor.execute(sql, (user_id,))
        return await cursor.fetchall()


async def get_user_stage_record(user_id: int, vs_stage_id: int) -> Optional[Dict[str, Any]]:
    """获取用户指定地图的胜率记录"""
    sql = "SELECT * FROM user_stage_record WHERE user_id = ? AND vs_stage_id = ?"
    async with get_cursor(commit=False) as cursor:
        await cursor.execute(sql, (user_id, vs_stage_id))
        return await cursor.fetchone()


async def upsert_stage_record(data: StageRecordData) -> Dict[str, Any]:
    """插入或更新地图胜率记录（以 user_id + vs_stage_id 判重）"""
    now = datetime.utcnow().isoformat()

    sql = """
    INSERT INTO user_stage_record (
        user_id, vs_stage_id, name, stage_id, stage_code,
        last_played_time, win_rate_ar, win_rate_cl, win_rate_gl, win_rate_lf, win_rate_tw,
        updated_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(user_id, vs_stage_id) DO UPDATE SET
        name = excluded.name,
        stage_id = excluded.stage_id,
        stage_code = excluded.stage_code,
        last_played_time = excluded.last_played_time,
        win_rate_ar = excluded.win_rate_ar,
        win_rate_cl = excluded.win_rate_cl,
        win_rate_gl = excluded.win_rate_gl,
        win_rate_lf = excluded.win_rate_lf,
        win_rate_tw = excluded.win_rate_tw,
        updated_at = excluded.updated_at
    """
    async with get_cursor() as cursor:
        await cursor.execute(sql, (
            data.user_id,
            data.vs_stage_id,
            data.name,
            data.stage_id,
            data.stage_code,
            data.last_played_time,
            data.win_rate_ar,
            data.win_rate_cl,
            data.win_rate_gl,
            data.win_rate_lf,
            data.win_rate_tw,
            now,
        ))
        await cursor.execute(
            "SELECT * FROM user_stage_record WHERE user_id = ? AND vs_stage_id = ?",
            (data.user_id, data.vs_stage_id)
        )
        return await cursor.fetchone()


async def batch_upsert_stage_records(records: List[StageRecordData]) -> int:
    """批量插入或更新地图胜率记录"""
    if not records:
        return 0

    now = datetime.utcnow().isoformat()

    sql = """
    INSERT INTO user_stage_record (
        user_id, vs_stage_id, name, stage_id, stage_code,
        last_played_time, win_rate_ar, win_rate_cl, win_rate_gl, win_rate_lf, win_rate_tw,
        updated_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(user_id, vs_stage_id) DO UPDATE SET
        name = excluded.name,
        stage_id = excluded.stage_id,
        stage_code = excluded.stage_code,
        last_played_time = excluded.last_played_time,
        win_rate_ar = excluded.win_rate_ar,
        win_rate_cl = excluded.win_rate_cl,
        win_rate_gl = excluded.win_rate_gl,
        win_rate_lf = excluded.win_rate_lf,
        win_rate_tw = excluded.win_rate_tw,
        updated_at = excluded.updated_at
    """

    async with get_connection() as conn:
        cursor = await conn.cursor()
        try:
            params = [
                (
                    data.user_id,
                    data.vs_stage_id,
                    data.name,
                    data.stage_id,
                    data.stage_code,
                    data.last_played_time,
                    data.win_rate_ar,
                    data.win_rate_cl,
                    data.win_rate_gl,
                    data.win_rate_lf,
                    data.win_rate_tw,
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
            await cursor.close()


async def delete_user_stage_records(user_id: int) -> int:
    """删除用户所有地图胜率记录"""
    async with get_cursor() as cursor:
        await cursor.execute("DELETE FROM user_stage_record WHERE user_id = ?", (user_id,))
        return cursor.rowcount
