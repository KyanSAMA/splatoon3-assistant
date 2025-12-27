"""用户数据访问层 (DAO)"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict, Any

from .connect import get_cursor, get_connection


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
    sql = "SELECT * FROM user WHERE is_current = 1 LIMIT 1"
    async with get_cursor(commit=False) as cursor:
        await cursor.execute(sql)
        return await cursor.fetchone()


async def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    """根据 ID 获取用户"""
    sql = "SELECT * FROM user WHERE id = ?"
    async with get_cursor(commit=False) as cursor:
        await cursor.execute(sql, (user_id,))
        return await cursor.fetchone()


async def get_user_by_splatoon_id(splatoon_id: str) -> Optional[Dict[str, Any]]:
    """根据 splatoon_id 获取用户"""
    sql = "SELECT * FROM user WHERE splatoon_id = ?"
    async with get_cursor(commit=False) as cursor:
        await cursor.execute(sql, (splatoon_id,))
        return await cursor.fetchone()


async def get_user_by_nsa_id(nsa_id: str) -> Optional[Dict[str, Any]]:
    """根据 nsa_id 获取用户"""
    sql = "SELECT * FROM user WHERE nsa_id = ?"
    async with get_cursor(commit=False) as cursor:
        await cursor.execute(sql, (nsa_id,))
        return await cursor.fetchone()


async def get_user_by_session_token(session_token: str) -> Optional[Dict[str, Any]]:
    """根据 session_token 获取用户"""
    sql = "SELECT * FROM user WHERE session_token = ?"
    async with get_cursor(commit=False) as cursor:
        await cursor.execute(sql, (session_token,))
        return await cursor.fetchone()


async def get_all_users() -> List[Dict[str, Any]]:
    """获取全部用户，按活跃时间倒序"""
    sql = "SELECT * FROM user ORDER BY is_current DESC, last_login_at DESC"
    async with get_cursor(commit=False) as cursor:
        await cursor.execute(sql)
        return await cursor.fetchall()


async def create_or_update_user(bundle: TokenBundle, mark_current: bool = True) -> Dict[str, Any]:
    """
    创建或更新用户（UPSERT，以 nsa_id 判重）

    Args:
        bundle: Token 数据包
        mark_current: 是否设为当前用户
    """
    now = datetime.utcnow().isoformat()

    async with get_connection() as conn:
        cursor = await conn.cursor()
        try:
            if mark_current:
                await cursor.execute("UPDATE user SET is_current = 0 WHERE is_current = 1")

            sql = """
            INSERT INTO user (
                nsa_id, splatoon_id, session_token, access_token, g_token, bullet_token,
                user_lang, user_country, user_nickname,
                is_current, last_login_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(nsa_id) DO UPDATE SET
                splatoon_id = excluded.splatoon_id,
                session_token = excluded.session_token,
                access_token = excluded.access_token,
                g_token = excluded.g_token,
                bullet_token = excluded.bullet_token,
                user_lang = excluded.user_lang,
                user_country = excluded.user_country,
                user_nickname = excluded.user_nickname,
                is_current = excluded.is_current,
                last_login_at = excluded.last_login_at,
                updated_at = excluded.updated_at
            """
            await cursor.execute(sql, (
                bundle.nsa_id,
                bundle.splatoon_id,
                bundle.session_token,
                bundle.access_token,
                bundle.g_token,
                bundle.bullet_token,
                bundle.user_lang,
                bundle.user_country,
                bundle.user_nickname,
                1 if mark_current else 0,
                now,
                now,
            ))

            await cursor.execute(
                "SELECT * FROM user WHERE nsa_id = ?",
                (bundle.nsa_id,)
            )
            row = await cursor.fetchone()
            await conn.commit()
            return row
        except Exception:
            await conn.rollback()
            raise
        finally:
            await cursor.close()


async def update_tokens(user_id: int, bundle: TokenBundle, touch_last_login: bool = True) -> Optional[Dict[str, Any]]:
    """
    更新用户 Token（原子操作）

    Args:
        user_id: 用户 ID
        bundle: Token 数据包
        touch_last_login: 是否更新 last_login_at
    """
    now = datetime.utcnow().isoformat()

    if touch_last_login:
        sql = """
        UPDATE user SET
            session_token = ?,
            access_token = ?,
            g_token = ?,
            bullet_token = ?,
            user_lang = ?,
            user_country = ?,
            user_nickname = ?,
            splatoon_id = COALESCE(?, splatoon_id),
            last_login_at = ?,
            updated_at = ?
        WHERE id = ?
        """
        params = (
            bundle.session_token,
            bundle.access_token,
            bundle.g_token,
            bundle.bullet_token,
            bundle.user_lang,
            bundle.user_country,
            bundle.user_nickname,
            bundle.splatoon_id,
            now,
            now,
            user_id,
        )
    else:
        sql = """
        UPDATE user SET
            session_token = ?,
            access_token = ?,
            g_token = ?,
            bullet_token = ?,
            user_lang = ?,
            user_country = ?,
            user_nickname = ?,
            splatoon_id = COALESCE(?, splatoon_id),
            updated_at = ?
        WHERE id = ?
        """
        params = (
            bundle.session_token,
            bundle.access_token,
            bundle.g_token,
            bundle.bullet_token,
            bundle.user_lang,
            bundle.user_country,
            bundle.user_nickname,
            bundle.splatoon_id,
            now,
            user_id,
        )

    async with get_cursor() as cursor:
        await cursor.execute(sql, params)
        await cursor.execute("SELECT * FROM user WHERE id = ?", (user_id,))
        return await cursor.fetchone()


async def set_current_user(user_id: int) -> Optional[Dict[str, Any]]:
    """
    切换当前用户（事务操作）

    Args:
        user_id: 目标用户 ID
    """
    now = datetime.utcnow().isoformat()

    async with get_connection() as conn:
        cursor = await conn.cursor()
        try:
            await cursor.execute("UPDATE user SET is_current = 0 WHERE is_current = 1")
            await cursor.execute(
                "UPDATE user SET is_current = 1, last_login_at = ?, updated_at = ? WHERE id = ?",
                (now, now, user_id)
            )
            if cursor.rowcount == 0:
                raise ValueError("指定的用户不存在")
            await cursor.execute("SELECT * FROM user WHERE id = ?", (user_id,))
            row = await cursor.fetchone()
            await conn.commit()
            return row
        except Exception:
            await conn.rollback()
            raise
        finally:
            await cursor.close()


async def delete_user(user_id: int) -> bool:
    """
    删除用户（硬删除）

    Args:
        user_id: 用户 ID

    Returns:
        是否删除成功
    """
    async with get_cursor() as cursor:
        await cursor.execute("DELETE FROM user WHERE id = ?", (user_id,))
        return cursor.rowcount > 0


async def clear_current_user() -> bool:
    """清除当前用户标志（登出）"""
    async with get_cursor() as cursor:
        await cursor.execute("UPDATE user SET is_current = 0 WHERE is_current = 1")
        return cursor.rowcount > 0