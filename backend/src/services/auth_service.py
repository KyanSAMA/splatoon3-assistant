"""认证服务 - FastAPI 路由"""

import asyncio
import logging
import secrets
import time
from typing import Dict, Optional, Tuple, List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..auth.nso_auth import NSOAuth
from ..api.splatnet3_api import SplatNet3API
from ..models import User
from ..dao.user_dao import (
    TokenBundle,
    create_or_update_user,
    get_current_user,
    get_all_users,
    set_current_user,
    clear_current_user,
    update_tokens,
    mark_session_expired,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])

# ============ 登录会话管理 ============
# state -> (nso_auth, verifier, created_at)
_pending_sessions: Dict[str, Tuple[NSOAuth, bytes, float]] = {}
_SESSION_TTL = 600  # 10 分钟过期

# ============ API 会话管理 ============
# user_id -> (api, last_access_time)
_user_api_sessions: Dict[int, Tuple[SplatNet3API, float]] = {}
_API_SESSION_TTL = 1800  # 30 分钟不活跃则释放
_sessions_lock = asyncio.Lock()  # 并发控制


# ============ 依赖注入 (类似 AOP) ============

async def require_current_user() -> User:
    """
    依赖：要求当前已登录用户

    使用方式：
        @router.get("/protected")
        async def protected_route(user: User = Depends(require_current_user)):
            return {"user": user.user_nickname}
    """
    row = await get_current_user()
    if not row:
        raise HTTPException(status_code=401, detail="未登录")
    user = User.from_dict(row)
    if not user:
        raise HTTPException(status_code=401, detail="未登录")
    # 检查 session 是否已过期
    if user.session_expired:
        raise HTTPException(
            status_code=401,
            detail={"code": "SESSION_EXPIRED", "message": "Session 已过期，请重新登录"}
        )
    return user


async def _cleanup_expired_api_sessions() -> None:
    """清理过期的 API 会话"""
    now = time.time()
    to_close: List[Tuple[int, SplatNet3API]] = []

    async with _sessions_lock:
        expired = [uid for uid, (_, ts) in _user_api_sessions.items() if now - ts > _API_SESSION_TTL]
        for uid in expired:
            if uid in _user_api_sessions:
                api, _ = _user_api_sessions.pop(uid)
                to_close.append((uid, api))

    for uid, api in to_close:
        try:
            await api.close()
            logger.debug(f"API session expired for user {uid}")
        except Exception as e:
            logger.error(f"Failed to close expired API session for user {uid}: {e}")


def _make_token_update_callback(user_id: int):
    """创建 token 更新回调（用于 API 自动刷新后持久化）"""

    async def callback(tokens: Dict):
        try:
            bundle = TokenBundle(
                nsa_id=tokens.get("nsa_id", ""),
                session_token=tokens.get("session_token", ""),
                access_token=tokens.get("access_token", ""),
                g_token=tokens.get("g_token", ""),
                bullet_token=tokens.get("bullet_token", ""),
                user_lang=tokens.get("user_lang", "zh-CN"),
                user_country=tokens.get("user_country", "JP"),
                user_nickname=tokens.get("user_nickname", ""),
            )
            await update_tokens(user_id, bundle)
            logger.info(f"Tokens refreshed and saved for user {user_id}")
        except Exception as e:
            logger.error(f"Failed to save refreshed tokens for user {user_id}: {e}")

    return callback


def _make_session_expired_callback(user_id: int):
    """创建 session 过期回调（用于标记数据库中用户 session 已过期）"""

    async def callback():
        try:
            await mark_session_expired(user_id)
            logger.warning(f"Session expired marked for user {user_id}")
        except Exception as e:
            logger.error(f"Failed to mark session expired for user {user_id}: {e}")
        # 清理 API 缓存
        try:
            await close_user_api_session(user_id)
            logger.debug(f"API session cleared after expiration for user {user_id}")
        except Exception as e:
            logger.error(f"Failed to close API session after expiration for user {user_id}: {e}")

    return callback


async def _get_or_create_api(user: User) -> SplatNet3API:
    """获取或创建用户的 API 实例（线程安全）"""
    await _cleanup_expired_api_sessions()

    api_to_close: Optional[SplatNet3API] = None

    async with _sessions_lock:
        existing = _user_api_sessions.get(user.id)
        if existing:
            cached_api, _ = existing
            # 检查 token 一致性
            if (cached_api.session_token == user.session_token
                    and cached_api.g_token == user.g_token
                    and cached_api.bullet_token == user.bullet_token):
                _user_api_sessions[user.id] = (cached_api, time.time())
                return cached_api
            # token 不一致，标记旧实例待关闭
            api_to_close = cached_api
            _user_api_sessions.pop(user.id, None)

        # 创建新的 API 实例
        nso_auth = NSOAuth()
        api = SplatNet3API(
            nso_auth=nso_auth,
            session_token=user.session_token,
            access_token=user.access_token,
            g_token=user.g_token,
            bullet_token=user.bullet_token,
            user_lang=user.user_lang,
            user_country=user.user_country,
            on_tokens_updated=_make_token_update_callback(user.id),
            on_session_expired=_make_session_expired_callback(user.id),
        )
        _user_api_sessions[user.id] = (api, time.time())
        logger.debug(f"API session created for user {user.id}")

    # 在锁外关闭旧实例
    if api_to_close:
        try:
            await api_to_close.close()
            logger.debug(f"Stale API session closed for user {user.id}")
        except Exception as e:
            logger.error(f"Failed to close stale API session for user {user.id}: {e}")

    return api


async def close_user_api_session(user_id: int) -> None:
    """关闭指定用户的 API 会话（线程安全）"""
    api_to_close = None
    async with _sessions_lock:
        if user_id in _user_api_sessions:
            api, _ = _user_api_sessions.pop(user_id)
            api_to_close = api

    if api_to_close:
        try:
            await api_to_close.close()
            logger.debug(f"API session closed for user {user_id}")
        except Exception as e:
            logger.error(f"Failed to close API session for user {user_id}: {e}")


async def require_splatnet_api(user: User = Depends(require_current_user)) -> SplatNet3API:
    """
    依赖：获取当前用户的 SplatNet3API 实例

    - 自动创建（如果不存在）
    - 自动刷新访问时间
    - Token 刷新后自动持久化

    使用方式：
        @router.get("/battles")
        async def get_battles(api: SplatNet3API = Depends(require_splatnet_api)):
            return await api.get_recent_battles()
    """
    return await _get_or_create_api(user)


async def close_all_api_sessions() -> None:
    """关闭所有 API 会话（应用关闭时调用）"""
    async with _sessions_lock:
        sessions = list(_user_api_sessions.items())
        _user_api_sessions.clear()

    for user_id, (api, _) in sessions:
        try:
            await api.close()
            logger.info(f"Closed API session for user {user_id}")
        except Exception as e:
            logger.error(f"Failed to close API session for user {user_id}: {e}")


class LoginStartResponse(BaseModel):
    """登录开始响应"""
    login_url: str
    state: str


class LoginCompleteRequest(BaseModel):
    """登录完成请求"""
    callback_url: str
    state: str


class UserResponse(BaseModel):
    """用户响应（不含敏感 token）"""
    id: int
    user_nickname: Optional[str]
    user_lang: str
    user_country: str
    is_current: bool
    last_login_at: str
    created_at: str


class SwitchUserRequest(BaseModel):
    """切换用户请求"""
    user_id: int


async def _cleanup_expired_sessions() -> None:
    """清理过期的登录会话并关闭连接"""
    now = time.time()
    expired = [k for k, (_, _, ts) in _pending_sessions.items() if now - ts > _SESSION_TTL]
    for k in expired:
        nso_auth, _, _ = _pending_sessions.pop(k)
        await nso_auth.close()


@router.get("/login", response_model=LoginStartResponse)
async def start_login():
    """
    开始登录流程

    返回 Nintendo 登录 URL 和 state 标识
    """
    await _cleanup_expired_sessions()

    nso_auth = NSOAuth()
    url, verifier = await nso_auth.login_in()

    state = secrets.token_urlsafe(16)
    _pending_sessions[state] = (nso_auth, verifier, time.time())
    print(f"[DEBUG] login: state={state}")

    return LoginStartResponse(login_url=url, state=state)


@router.post("/callback", response_model=UserResponse)
async def complete_login(req: LoginCompleteRequest):
    """
    完成登录流程

    接收 NSO 回调 URL，完成认证并保存用户
    """
    entry = _pending_sessions.pop(req.state, None)
    if not entry:
        print(f"[DEBUG] callback: state={req.state} not found")
        raise HTTPException(status_code=400, detail="Invalid or expired state")

    nso_auth, verifier, created_at = entry
    if time.time() - created_at > _SESSION_TTL:
        await nso_auth.close()
        print(f"[DEBUG] callback: state={req.state} expired")
        raise HTTPException(status_code=400, detail="State expired, please login again")

    print(f"[DEBUG] callback: state={req.state}")

    try:
        session_token = await nso_auth.login_in_2(req.callback_url, verifier)
        if not session_token:
            raise HTTPException(status_code=400, detail="Failed to obtain session_token")

        access_token, g_token, nickname, lang, country, user_info = await nso_auth.get_gtoken(session_token)
        nsa_id = user_info["nsaId"]

        bullet_token = await nso_auth.get_bullet(g_token)
        if not bullet_token:
            raise HTTPException(status_code=400, detail="Failed to obtain bullet_token")

        bundle = TokenBundle(
            nsa_id=nsa_id,
            session_token=session_token,
            access_token=access_token,
            g_token=g_token,
            bullet_token=bullet_token,
            user_lang=lang,
            user_country=country,
            user_nickname=nickname,
            splatoon_id=None,
        )

        row = await create_or_update_user(bundle, mark_current=True)
        user = User.from_dict(row)
        if not user:
            raise HTTPException(status_code=500, detail="持久化用户失败")

        return UserResponse(
            id=user.id,
            user_nickname=user.user_nickname,
            user_lang=user.user_lang,
            user_country=user.user_country,
            is_current=user.is_current,
            last_login_at=user.last_login_at,
            created_at=user.created_at,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await nso_auth.close()


@router.get("/current", response_model=Optional[UserResponse])
async def get_current():
    """获取当前登录用户"""
    row = await get_current_user()
    if not row:
        return None

    user = User.from_dict(row)
    if not user:
        return None

    return UserResponse(
        id=user.id,
        user_nickname=user.user_nickname,
        user_lang=user.user_lang,
        user_country=user.user_country,
        is_current=user.is_current,
        last_login_at=user.last_login_at,
        created_at=user.created_at,
    )


@router.get("/users", response_model=list[UserResponse])
async def list_users():
    """获取全部用户，按活跃时间倒序"""
    rows = await get_all_users()
    result = []
    for row in rows:
        user = User.from_dict(row)
        if user:
            result.append(UserResponse(
                id=user.id,
                user_nickname=user.user_nickname,
                user_lang=user.user_lang,
                user_country=user.user_country,
                is_current=user.is_current,
                last_login_at=user.last_login_at,
                created_at=user.created_at,
            ))
    return result


@router.post("/switch", response_model=UserResponse)
async def switch_user(req: SwitchUserRequest):
    """切换当前用户（关闭旧用户的 API 会话）"""
    # 关闭旧用户的 API 会话
    old_row = await get_current_user()
    if old_row:
        old_user = User.from_dict(old_row)
        if old_user and old_user.id != req.user_id:
            await close_user_api_session(old_user.id)

    try:
        row = await set_current_user(req.user_id)
        if not row:
            raise HTTPException(status_code=404, detail="用户不存在")

        user = User.from_dict(row)
        return UserResponse(
            id=user.id,
            user_nickname=user.user_nickname,
            user_lang=user.user_lang,
            user_country=user.user_country,
            is_current=user.is_current,
            last_login_at=user.last_login_at,
            created_at=user.created_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/logout")
async def logout():
    """登出当前用户（清除 is_current 标志并释放 API 资源）"""
    row = await get_current_user()
    if row:
        user = User.from_dict(row)
        if user:
            await close_user_api_session(user.id)
    await clear_current_user()
    return {"success": True}
