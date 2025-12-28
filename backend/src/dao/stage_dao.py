"""地图数据访问层 (DAO)"""

from typing import Optional, List, Dict, Any

from .connect import get_cursor


async def get_stage_by_vs_stage_id(vs_stage_id: int) -> Optional[Dict[str, Any]]:
    """通过 vs_stage_id 获取地图"""
    sql = "SELECT * FROM stage WHERE vs_stage_id = ?"
    async with get_cursor(commit=False) as cursor:
        await cursor.execute(sql, (vs_stage_id,))
        return await cursor.fetchone()


async def get_stage_by_id(stage_id: int) -> Optional[Dict[str, Any]]:
    """通过 id 获取地图"""
    sql = "SELECT * FROM stage WHERE id = ?"
    async with get_cursor(commit=False) as cursor:
        await cursor.execute(sql, (stage_id,))
        return await cursor.fetchone()


async def get_stage_by_code(code: str) -> Optional[Dict[str, Any]]:
    """通过 code 获取地图"""
    sql = "SELECT * FROM stage WHERE code = ?"
    async with get_cursor(commit=False) as cursor:
        await cursor.execute(sql, (code,))
        return await cursor.fetchone()


async def get_all_stages(stage_type: Optional[str] = None) -> List[Dict[str, Any]]:
    """获取所有地图，可按类型筛选"""
    if stage_type:
        sql = "SELECT * FROM stage WHERE stage_type = ? ORDER BY id"
        params = (stage_type,)
    else:
        sql = "SELECT * FROM stage ORDER BY id"
        params = ()
    async with get_cursor(commit=False) as cursor:
        await cursor.execute(sql, params)
        return await cursor.fetchall()


async def get_vs_stages() -> List[Dict[str, Any]]:
    """获取所有对战地图"""
    return await get_all_stages(stage_type="VS")


async def get_stages_map_by_vs_stage_id() -> Dict[int, Dict[str, Any]]:
    """获取 vs_stage_id -> stage 的映射字典"""
    stages = await get_vs_stages()
    return {s["vs_stage_id"]: s for s in stages if s.get("vs_stage_id")}
