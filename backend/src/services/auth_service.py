"""认证服务 - FastAPI 路由"""

import secrets
import time
from typing import Dict, Optional, Tuple

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..auth.nso_auth import NSOAuth
from ..models import User
from ..dao.user_dao import (
    TokenBundle,
    create_or_update_user,
    get_current_user,
    get_all_users,
    set_current_user,
    clear_current_user,
)

router = APIRouter(prefix="/auth", tags=["auth"])

# state -> (nso_auth, verifier, created_at)，每次登录使用独立的 NSOAuth 实例
_pending_sessions: Dict[str, Tuple[NSOAuth, bytes, float]] = {}
_SESSION_TTL = 600  # 10 分钟过期


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
    nsa_id: str
    splatoon_id: Optional[str]
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
        nsa_id = user_info["nsaid"]

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
            nsa_id=user.nsa_id,
            splatoon_id=user.splatoon_id,
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
        nsa_id=user.nsa_id,
        splatoon_id=user.splatoon_id,
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
                nsa_id=user.nsa_id,
                splatoon_id=user.splatoon_id,
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
    """切换当前用户"""
    try:
        row = await set_current_user(req.user_id)
        if not row:
            raise HTTPException(status_code=404, detail="用户不存在")

        user = User.from_dict(row)
        return UserResponse(
            id=user.id,
            nsa_id=user.nsa_id,
            splatoon_id=user.splatoon_id,
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
    """登出当前用户（清除 is_current 标志）"""
    await clear_current_user()
    return {"success": True}
