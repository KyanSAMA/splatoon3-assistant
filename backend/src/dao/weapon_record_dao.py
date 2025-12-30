"""用户武器战绩数据访问层 (DAO) - SQLAlchemy 2.0"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict, Any

from sqlalchemy import select, delete
from sqlalchemy.dialects.sqlite import insert

from .database import get_session
from .models.user import UserWeaponRecord


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
    async with get_session() as session:
        stmt = select(UserWeaponRecord).where(
            UserWeaponRecord.user_id == user_id
        ).order_by(UserWeaponRecord.main_weapon_id)
        result = await session.execute(stmt)
        records = result.scalars().all()
        return [r.to_dict() for r in records]


async def get_user_weapon_record(user_id: int, main_weapon_id: int) -> Optional[Dict[str, Any]]:
    """获取用户指定武器的战绩"""
    async with get_session() as session:
        stmt = select(UserWeaponRecord).where(
            UserWeaponRecord.user_id == user_id,
            UserWeaponRecord.main_weapon_id == main_weapon_id,
        )
        result = await session.execute(stmt)
        record = result.scalar_one_or_none()
        return record.to_dict() if record else None


async def upsert_weapon_record(data: WeaponRecordData) -> Dict[str, Any]:
    """插入或更新武器战绩（以 user_id + main_weapon_id 判重）"""
    now = datetime.utcnow().isoformat()

    async with get_session() as session:
        stmt = insert(UserWeaponRecord).values(
            user_id=data.user_id,
            main_weapon_id=data.main_weapon_id,
            main_weapon_name=data.main_weapon_name,
            last_used_time=data.last_used_time,
            level=data.level,
            exp_to_level_up=data.exp_to_level_up,
            win=data.win,
            vibes=data.vibes,
            paint=data.paint,
            current_weapon_power=data.current_weapon_power,
            max_weapon_power=data.max_weapon_power,
            created_at=now,
            updated_at=now,
        ).on_conflict_do_update(
            index_elements=["user_id", "main_weapon_id"],
            set_={
                "main_weapon_name": data.main_weapon_name,
                "last_used_time": data.last_used_time,
                "level": data.level,
                "exp_to_level_up": data.exp_to_level_up,
                "win": data.win,
                "vibes": data.vibes,
                "paint": data.paint,
                "current_weapon_power": data.current_weapon_power,
                "max_weapon_power": data.max_weapon_power,
                "updated_at": now,
            },
        )
        await session.execute(stmt)
        await session.flush()

        query = select(UserWeaponRecord).where(
            UserWeaponRecord.user_id == data.user_id,
            UserWeaponRecord.main_weapon_id == data.main_weapon_id,
        )
        result = await session.execute(query)
        record = result.scalar_one()
        return record.to_dict()


async def batch_upsert_weapon_records(records: List[WeaponRecordData]) -> int:
    """批量插入或更新武器战绩"""
    if not records:
        return 0

    now = datetime.utcnow().isoformat()

    async with get_session() as session:
        for data in records:
            stmt = insert(UserWeaponRecord).values(
                user_id=data.user_id,
                main_weapon_id=data.main_weapon_id,
                main_weapon_name=data.main_weapon_name,
                last_used_time=data.last_used_time,
                level=data.level,
                exp_to_level_up=data.exp_to_level_up,
                win=data.win,
                vibes=data.vibes,
                paint=data.paint,
                current_weapon_power=data.current_weapon_power,
                max_weapon_power=data.max_weapon_power,
                created_at=now,
                updated_at=now,
            ).on_conflict_do_update(
                index_elements=["user_id", "main_weapon_id"],
                set_={
                    "main_weapon_name": data.main_weapon_name,
                    "last_used_time": data.last_used_time,
                    "level": data.level,
                    "exp_to_level_up": data.exp_to_level_up,
                    "win": data.win,
                    "vibes": data.vibes,
                    "paint": data.paint,
                    "current_weapon_power": data.current_weapon_power,
                    "max_weapon_power": data.max_weapon_power,
                    "updated_at": now,
                },
            )
            await session.execute(stmt)

        return len(records)


async def delete_user_weapon_records(user_id: int) -> int:
    """删除用户所有武器战绩"""
    async with get_session() as session:
        stmt = delete(UserWeaponRecord).where(UserWeaponRecord.user_id == user_id)
        result = await session.execute(stmt)
        return result.rowcount
