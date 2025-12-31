"""用户数据访问层 (DAO) - SQLAlchemy 2.0"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict, Any

from sqlalchemy import select, update, delete
from sqlalchemy.dialects.sqlite import insert

from .database import get_session
from .models.user import User


@dataclass
class TokenBundle:
    """Token 数据包"""
    nsa_id: str
    session_token: str
    access_token: str
    g_token: str
    bullet_token: str
    user_lang: str
    user_country: str
    user_nickname: str
    splatoon_id: Optional[str] = None


async def get_current_user() -> Optional[Dict[str, Any]]:
    """获取当前用户"""
    async with get_session() as session:
        stmt = select(User).where(User.is_current == 1).limit(1)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        return user.to_dict() if user else None


async def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    """根据 ID 获取用户"""
    async with get_session() as session:
        user = await session.get(User, user_id)
        return user.to_dict() if user else None


async def get_user_by_splatoon_id(splatoon_id: str) -> Optional[Dict[str, Any]]:
    """根据 splatoon_id 获取用户"""
    async with get_session() as session:
        stmt = select(User).where(User.splatoon_id == splatoon_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        return user.to_dict() if user else None


async def get_user_by_nsa_id(nsa_id: str) -> Optional[Dict[str, Any]]:
    """根据 nsa_id 获取用户"""
    async with get_session() as session:
        stmt = select(User).where(User.nsa_id == nsa_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        return user.to_dict() if user else None


async def get_user_by_session_token(session_token: str) -> Optional[Dict[str, Any]]:
    """根据 session_token 获取用户"""
    async with get_session() as session:
        stmt = select(User).where(User.session_token == session_token)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        return user.to_dict() if user else None


async def get_all_users() -> List[Dict[str, Any]]:
    """获取全部用户，按活跃时间倒序"""
    async with get_session() as session:
        stmt = select(User).order_by(User.is_current.desc(), User.last_login_at.desc())
        result = await session.execute(stmt)
        users = result.scalars().all()
        return [u.to_dict() for u in users]


async def create_or_update_user(bundle: TokenBundle, mark_current: bool = True) -> Dict[str, Any]:
    """创建或更新用户（UPSERT，以 nsa_id 判重）"""
    now = datetime.utcnow().isoformat()

    async with get_session() as session:
        if mark_current:
            await session.execute(
                update(User).where(User.is_current == 1).values(is_current=0)
            )

        stmt = insert(User).values(
            nsa_id=bundle.nsa_id,
            splatoon_id=bundle.splatoon_id,
            session_token=bundle.session_token,
            access_token=bundle.access_token,
            g_token=bundle.g_token,
            bullet_token=bundle.bullet_token,
            user_lang=bundle.user_lang,
            user_country=bundle.user_country,
            user_nickname=bundle.user_nickname,
            is_current=1 if mark_current else 0,
            session_expired=0,
            last_login_at=now,
            created_at=now,
            updated_at=now,
        ).on_conflict_do_update(
            index_elements=["nsa_id"],
            set_={
                "splatoon_id": bundle.splatoon_id,
                "session_token": bundle.session_token,
                "access_token": bundle.access_token,
                "g_token": bundle.g_token,
                "bullet_token": bundle.bullet_token,
                "user_lang": bundle.user_lang,
                "user_country": bundle.user_country,
                "user_nickname": bundle.user_nickname,
                "is_current": 1 if mark_current else 0,
                "session_expired": 0,
                "last_login_at": now,
                "updated_at": now,
            },
        )
        await session.execute(stmt)
        await session.flush()

        # 重新查询返回完整数据
        query = select(User).where(User.nsa_id == bundle.nsa_id)
        result = await session.execute(query)
        user = result.scalar_one()
        return user.to_dict()


async def update_tokens(user_id: int, bundle: TokenBundle, touch_last_login: bool = True) -> Optional[Dict[str, Any]]:
    """更新用户 Token（原子操作）"""
    now = datetime.utcnow().isoformat()

    values: Dict[str, Any] = {
        "session_token": bundle.session_token,
        "access_token": bundle.access_token,
        "g_token": bundle.g_token,
        "bullet_token": bundle.bullet_token,
        "user_lang": bundle.user_lang,
        "user_country": bundle.user_country,
        "user_nickname": bundle.user_nickname,
        "updated_at": now,
    }

    if touch_last_login:
        values["last_login_at"] = now

    if bundle.splatoon_id is not None:
        values["splatoon_id"] = bundle.splatoon_id

    async with get_session() as session:
        stmt = update(User).where(User.id == user_id).values(**values)
        await session.execute(stmt)
        await session.flush()

        user = await session.get(User, user_id)
        return user.to_dict() if user else None


async def set_current_user(user_id: int) -> Optional[Dict[str, Any]]:
    """切换当前用户（事务操作）"""
    now = datetime.utcnow().isoformat()

    async with get_session() as session:
        # 清除当前用户标志
        await session.execute(
            update(User).where(User.is_current == 1).values(is_current=0)
        )

        # 设置新的当前用户
        stmt = update(User).where(User.id == user_id).values(
            is_current=1,
            last_login_at=now,
            updated_at=now,
        )
        result = await session.execute(stmt)

        if result.rowcount == 0:
            raise ValueError("指定的用户不存在")

        await session.flush()
        user = await session.get(User, user_id)
        return user.to_dict() if user else None


async def delete_user(user_id: int) -> bool:
    """删除用户（硬删除）"""
    async with get_session() as session:
        stmt = delete(User).where(User.id == user_id)
        result = await session.execute(stmt)
        return result.rowcount > 0


async def clear_current_user() -> bool:
    """清除当前用户标志（登出）"""
    async with get_session() as session:
        stmt = update(User).where(User.is_current == 1).values(is_current=0)
        result = await session.execute(stmt)
        return result.rowcount > 0


async def mark_session_expired(user_id: int) -> bool:
    """标记用户 session 已过期"""
    now = datetime.utcnow().isoformat()
    async with get_session() as session:
        stmt = update(User).where(User.id == user_id).values(
            session_expired=1,
            updated_at=now,
        )
        result = await session.execute(stmt)
        return result.rowcount > 0


async def clear_session_expired(user_id: int) -> bool:
    """清除用户 session 过期标记（重新登录后调用）"""
    now = datetime.utcnow().isoformat()
    async with get_session() as session:
        stmt = update(User).where(User.id == user_id).values(
            session_expired=0,
            updated_at=now,
        )
        result = await session.execute(stmt)
        return result.rowcount > 0
