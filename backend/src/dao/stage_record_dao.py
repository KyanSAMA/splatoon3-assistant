"""用户地图胜率数据访问层 (DAO) - SQLAlchemy 2.0"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict, Any

from sqlalchemy import select, delete
from sqlalchemy.dialects.sqlite import insert

from .database import get_session
from .models.user import UserStageRecord


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
    async with get_session() as session:
        stmt = select(UserStageRecord).where(
            UserStageRecord.user_id == user_id
        ).order_by(UserStageRecord.vs_stage_id)
        result = await session.execute(stmt)
        records = result.scalars().all()
        return [r.to_dict() for r in records]


async def get_user_stage_record(user_id: int, vs_stage_id: int) -> Optional[Dict[str, Any]]:
    """获取用户指定地图的胜率记录"""
    async with get_session() as session:
        stmt = select(UserStageRecord).where(
            UserStageRecord.user_id == user_id,
            UserStageRecord.vs_stage_id == vs_stage_id,
        )
        result = await session.execute(stmt)
        record = result.scalar_one_or_none()
        return record.to_dict() if record else None


async def upsert_stage_record(data: StageRecordData) -> Dict[str, Any]:
    """插入或更新地图胜率记录（以 user_id + vs_stage_id 判重）"""
    now = datetime.utcnow().isoformat()

    async with get_session() as session:
        stmt = insert(UserStageRecord).values(
            user_id=data.user_id,
            vs_stage_id=data.vs_stage_id,
            name=data.name,
            stage_id=data.stage_id,
            stage_code=data.stage_code,
            last_played_time=data.last_played_time,
            win_rate_ar=data.win_rate_ar,
            win_rate_cl=data.win_rate_cl,
            win_rate_gl=data.win_rate_gl,
            win_rate_lf=data.win_rate_lf,
            win_rate_tw=data.win_rate_tw,
            created_at=now,
            updated_at=now,
        ).on_conflict_do_update(
            index_elements=["user_id", "vs_stage_id"],
            set_={
                "name": data.name,
                "stage_id": data.stage_id,
                "stage_code": data.stage_code,
                "last_played_time": data.last_played_time,
                "win_rate_ar": data.win_rate_ar,
                "win_rate_cl": data.win_rate_cl,
                "win_rate_gl": data.win_rate_gl,
                "win_rate_lf": data.win_rate_lf,
                "win_rate_tw": data.win_rate_tw,
                "updated_at": now,
            },
        )
        await session.execute(stmt)
        await session.flush()

        query = select(UserStageRecord).where(
            UserStageRecord.user_id == data.user_id,
            UserStageRecord.vs_stage_id == data.vs_stage_id,
        )
        result = await session.execute(query)
        record = result.scalar_one()
        return record.to_dict()


async def batch_upsert_stage_records(records: List[StageRecordData]) -> int:
    """批量插入或更新地图胜率记录"""
    if not records:
        return 0

    now = datetime.utcnow().isoformat()

    async with get_session() as session:
        for data in records:
            stmt = insert(UserStageRecord).values(
                user_id=data.user_id,
                vs_stage_id=data.vs_stage_id,
                name=data.name,
                stage_id=data.stage_id,
                stage_code=data.stage_code,
                last_played_time=data.last_played_time,
                win_rate_ar=data.win_rate_ar,
                win_rate_cl=data.win_rate_cl,
                win_rate_gl=data.win_rate_gl,
                win_rate_lf=data.win_rate_lf,
                win_rate_tw=data.win_rate_tw,
                created_at=now,
                updated_at=now,
            ).on_conflict_do_update(
                index_elements=["user_id", "vs_stage_id"],
                set_={
                    "name": data.name,
                    "stage_id": data.stage_id,
                    "stage_code": data.stage_code,
                    "last_played_time": data.last_played_time,
                    "win_rate_ar": data.win_rate_ar,
                    "win_rate_cl": data.win_rate_cl,
                    "win_rate_gl": data.win_rate_gl,
                    "win_rate_lf": data.win_rate_lf,
                    "win_rate_tw": data.win_rate_tw,
                    "updated_at": now,
                },
            )
            await session.execute(stmt)

        return len(records)


async def delete_user_stage_records(user_id: int) -> int:
    """删除用户所有地图胜率记录"""
    async with get_session() as session:
        stmt = delete(UserStageRecord).where(UserStageRecord.user_id == user_id)
        result = await session.execute(stmt)
        return result.rowcount
