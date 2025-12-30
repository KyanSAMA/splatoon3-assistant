"""地图数据访问层 (DAO) - SQLAlchemy 2.0"""

from typing import Optional, List, Dict, Any

from sqlalchemy import select

from .database import get_session
from .models.stage import Stage


async def get_stage_by_vs_stage_id(vs_stage_id: int) -> Optional[Dict[str, Any]]:
    """通过 vs_stage_id 获取地图"""
    async with get_session() as session:
        stmt = select(Stage).where(Stage.vs_stage_id == vs_stage_id)
        result = await session.execute(stmt)
        stage = result.scalar_one_or_none()
        return stage.to_dict() if stage else None


async def get_stage_by_id(stage_id: int) -> Optional[Dict[str, Any]]:
    """通过 id 获取地图"""
    async with get_session() as session:
        stage = await session.get(Stage, stage_id)
        return stage.to_dict() if stage else None


async def get_stage_by_code(code: str) -> Optional[Dict[str, Any]]:
    """通过 code 获取地图"""
    async with get_session() as session:
        stmt = select(Stage).where(Stage.code == code)
        result = await session.execute(stmt)
        stage = result.scalar_one_or_none()
        return stage.to_dict() if stage else None


async def get_all_stages(stage_type: Optional[str] = None) -> List[Dict[str, Any]]:
    """获取所有地图，可按类型筛选"""
    async with get_session() as session:
        stmt = select(Stage).order_by(Stage.id)
        if stage_type:
            stmt = stmt.where(Stage.stage_type == stage_type)
        result = await session.execute(stmt)
        stages = result.scalars().all()
        return [s.to_dict() for s in stages]


async def get_vs_stages() -> List[Dict[str, Any]]:
    """获取所有对战地图"""
    return await get_all_stages(stage_type="VS")


async def get_stages_map_by_vs_stage_id() -> Dict[int, Dict[str, Any]]:
    """获取 vs_stage_id -> stage 的映射字典"""
    stages = await get_vs_stages()
    return {s["vs_stage_id"]: s for s in stages if s.get("vs_stage_id")}
