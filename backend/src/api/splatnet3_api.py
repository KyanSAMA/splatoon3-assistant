# SplatNet3 API module
# Based on reference-project/splatoon3-nso/s3s/splatoon.py (Splatoon class)
"""SplatNet3 GraphQL API wrapper with auto token refresh."""

import asyncio
import base64
import functools
import logging
from typing import Optional, Dict, Any, Callable, Tuple

logger = logging.getLogger(__name__)

from ..auth.nso_auth import NSOAuth, APP_USER_AGENT
from .graphql_utils import gen_graphql_body, GRAPHQL_URL
from ..core.config import Config, default_config
from ..core.http_client import AsyncHttpClient
from ..core.exceptions import (
    SessionExpiredError,
    MembershipRequiredError,
    BulletTokenError,
    TokenRefreshError,
    NetworkError
)


class _RefreshCycle:
    """刷新周期对象，隔离每次刷新的状态"""
    __slots__ = ('event', 'error')

    def __init__(self):
        self.event = asyncio.Event()
        self.error: Optional[BaseException] = None


class _RequestCycle:
    """请求周期对象，用于复用请求结果"""
    __slots__ = ('event', 'result', 'error')

    def __init__(self):
        self.event = asyncio.Event()
        self.result: Any = None
        self.error: Optional[BaseException] = None


def _request_lock(func):
    """
    请求去重装饰器

    如果相同请求正在进行中，等待其完成并复用结果，避免重复执行。
    """
    @functools.wraps(func)
    async def wrapper(self, *args, **kwargs):
        key = (func.__name__, args, tuple(sorted(kwargs.items())))
        # 生成可读的请求标识
        if func.__name__ == "request" and args:
            try:
                import json
                body = json.loads(args[0])
                req_id = body.get("extensions", {}).get("persistedQuery", {}).get("sha256Hash", "")[:8] or "unknown"
            except:
                req_id = "parse_error"
        elif func.__name__ == "ns_request" and args:
            req_id = args[0].split("/")[-1] if args[0] else "unknown"
        else:
            req_id = str(args)[:50]

        if key in self._request_cycles:
            cycle = self._request_cycles[key]
            logger.info(f"[RequestLock] 检测到相同请求，等待: {func.__name__}({req_id})")
            await cycle.event.wait()
            if cycle.error:
                logger.info(f"[RequestLock] 等待完成，原请求失败: {func.__name__}({req_id})")
                raise cycle.error
            logger.info(f"[RequestLock] 等待完成，复用结果: {func.__name__}({req_id})")
            return cycle.result

        cycle = _RequestCycle()
        self._request_cycles[key] = cycle
        logger.info(f"[RequestLock] 获得执行权: {func.__name__}({req_id})")
        try:
            result = await func(self, *args, **kwargs)
            cycle.result = result
            logger.info(f"[RequestLock] 执行完成: {func.__name__}({req_id})")
            return result
        except BaseException as e:
            cycle.error = e
            logger.info(f"[RequestLock] 执行异常: {func.__name__}({req_id}) - {type(e).__name__}")
            raise
        finally:
            cycle.event.set()
            self._request_cycles.pop(key, None)

    return wrapper


class SplatNet3API:
    """
    SplatNet3 GraphQL API client with auto token refresh

    借鉴 splatoon3-nso 的 Splatoon 类，增加了：
    - Token 过期自动刷新
    - 401 错误自动重试
    - 并发刷新控制（asyncio.Lock）
    - 持久化回调机制

    Usage:
        # 方式1：带自动刷新（推荐）
        api = SplatNet3API(
            nso_auth=NSOAuth(),
            session_token="...",
            g_token="...",
            bullet_token="...",
            on_tokens_updated=lambda tokens: print(tokens)
        )
        battles = await api.get_recent_battles()  # 自动处理 401

        # 方式2：简单模式（无自动刷新）
        api = SplatNet3API.simple(g_token="...", bullet_token="...")
        battles = await api.get_recent_battles()
    """

    def __init__(
        self,
        nso_auth: Optional[NSOAuth] = None,
        session_token: Optional[str] = None,
        access_token: Optional[str] = None,
        g_token: Optional[str] = None,
        bullet_token: Optional[str] = None,
        user_lang: str = "zh-CN",
        user_country: str = "JP",
        on_tokens_updated: Optional[Callable[[Dict[str, Any]], None]] = None,
        on_session_expired: Optional[Callable[[], None]] = None,
        config: Optional[Config] = None,
    ):
        """
        初始化 SplatNet3API

        Args:
            nso_auth: NSOAuth 实例（用于刷新 token）
            session_token: Nintendo session token
            access_token: Nintendo nso api token
            g_token: Game web token
            bullet_token: Bullet token
            user_lang: 用户语言
            user_country: 用户国家
            on_tokens_updated: Token 更新回调函数，参数为包含新 token 的字典
            on_session_expired: Session 过期回调函数（用于标记数据库）
            config: HTTP 配置
        """
        self.nso_auth = nso_auth
        self.session_token = session_token
        self.access_token = access_token
        self.g_token = g_token
        self.bullet_token = bullet_token
        self.user_lang = user_lang
        self.user_country = user_country
        self.on_tokens_updated = on_tokens_updated
        self.on_session_expired = on_session_expired
        self.config = config or default_config

        self._client: Optional[AsyncHttpClient] = None
        self._refresh_lock = asyncio.Lock()  # 防止并发刷新
        self._current_cycle: Optional[_RefreshCycle] = None  # 当前刷新周期
        self._is_refreshing = False  # 标记是否正在刷新
        self._request_cycles: Dict[Tuple, _RequestCycle] = {}  # 请求去重

    @classmethod
    def simple(
        cls,
        g_token: str,
        bullet_token: str,
        user_lang: str = "zh-CN",
        user_country: str = "JP",
        config: Optional[Config] = None,
    ) -> "SplatNet3API":
        """
        创建简单模式的 API 实例（无自动刷新功能）

        Args:
            g_token: Game web token
            bullet_token: Bullet token
            user_lang: 用户语言
            user_country: 用户国家
            config: HTTP 配置

        Returns:
            SplatNet3API 实例
        """
        return cls(
            nso_auth=None,
            session_token=None,
            g_token=g_token,
            bullet_token=bullet_token,
            user_lang=user_lang,
            user_country=user_country,
            on_tokens_updated=None,
            config=config,
        )

    def _get_client(self) -> AsyncHttpClient:
        """Get or create async HTTP client."""
        if self._client is None:
            self._client = AsyncHttpClient(self.config)
        return self._client

    def _can_auto_refresh(self) -> bool:
        """检查是否可以自动刷新 token"""
        return bool(self.nso_auth and self.session_token)

    async def _refresh_tokens(self) -> tuple[bool, Optional[Dict[str, Any]]]:
        """
        刷新 g_token 和 bullet_token（参照 splatoon3-nso 的 refresh_gtoken_and_bullettoken）

        使用独立刷新周期对象实现并发控制：
        - 每个刷新周期有独立的 event 和 error
        - 等待者持有周期引用，不受新周期影响
        - 避免竞态条件导致错误丢失

        Returns:
            (success, token_data) 元组：
            - success: 刷新是否成功
            - token_data: 新的 token 数据（如果成功），供回调使用

        Raises:
            SessionExpiredError: session_token 过期，需要重新登录
            MembershipRequiredError: NSO 会员过期
            BulletTokenError: Bullet token 获取失败（版本过时/封禁等）
            TokenRefreshError: 其他刷新失败原因
        """
        if not self._can_auto_refresh():
            raise TokenRefreshError("无法自动刷新：缺少 NSOAuth 或 session_token")

        # 检查是否需要等待其他协程完成刷新
        cycle_to_wait: Optional[_RefreshCycle] = None
        logger.info("[TokenRefresh] 获取刷新锁...")
        async with self._refresh_lock:
            if self._is_refreshing:
                # 已有协程在刷新，保存当前周期引用
                cycle_to_wait = self._current_cycle
                logger.info("[TokenRefresh] 检测到刷新进行中，将等待当前周期完成")
            else:
                # 获得刷新权，创建新周期
                self._is_refreshing = True
                self._current_cycle = _RefreshCycle()
                logger.info("[TokenRefresh] 获得刷新权，开始新周期")

        # 如果需要等待，则在锁外等待刷新完成
        if cycle_to_wait:
            logger.info("[TokenRefresh] 等待刷新周期完成...")
            await cycle_to_wait.event.wait()
            logger.info("[TokenRefresh] 刷新周期已完成，检查结果")
            # 检查该周期的刷新是否成功（不受新周期影响）
            if cycle_to_wait.error:
                raise cycle_to_wait.error
            return (True, None)  # 复用已刷新的 token

        # 执行刷新
        my_cycle = self._current_cycle
        try:
            logger.info("[TokenRefresh] 开始刷新 tokens...")

            # Step 1: 刷新 g_token
            access_token, g_token, nickname, lang, country, user_info = \
                await self.nso_auth.get_gtoken(self.session_token)

            if not g_token:
                raise TokenRefreshError("Failed to get g_token")

            # Step 2: 刷新 bullet_token（可能抛出 BulletTokenError）
            bullet_token = await self.nso_auth.get_bullet(g_token)

            if not bullet_token:
                raise TokenRefreshError("Failed to get bullet_token")

            # Step 3: 更新内存中的 token
            self.access_token = access_token
            self.g_token = g_token
            self.bullet_token = bullet_token
            self.user_lang = lang
            self.user_country = country

            logger.info("[TokenRefresh] Tokens 刷新成功")

            # Step 4: 返回 token 数据（回调将在锁外执行）
            token_data = {
                "session_token": self.session_token,
                "g_token": g_token,
                "bullet_token": bullet_token,
                "access_token": access_token,
                "user_lang": lang,
                "user_country": country,
                "user_nickname": nickname,
                "user_info": user_info,
            }

            return (True, token_data)

        except SessionExpiredError as e:
            my_cycle.error = e
            # 调用 session 过期回调（标记数据库）
            if self.on_session_expired:
                try:
                    if asyncio.iscoroutinefunction(self.on_session_expired):
                        await self.on_session_expired()
                    else:
                        self.on_session_expired()
                except Exception as cb_err:
                    logger.error(f"Session 过期回调失败: {cb_err}")
            raise
        except (MembershipRequiredError, BulletTokenError) as e:
            my_cycle.error = e
            raise
        except Exception as e:
            error = TokenRefreshError(f"Token 刷新失败: {e}")
            my_cycle.error = error
            raise error
        finally:
            logger.info("[TokenRefresh] 获取锁以释放刷新状态...")
            async with self._refresh_lock:
                self._is_refreshing = False
                my_cycle.event.set()  # 通知所有等待该周期的协程
                logger.info("[TokenRefresh] 刷新周期结束，已通知等待者")

    def head_bullet(self, force_lang: Optional[str] = None, force_country: Optional[str] = None) -> Dict[str, str]:
        """构建请求 headers（参照 Splatoon.head_bullet()）"""
        if force_lang:
            lang = force_lang
            country = force_country or self.user_country
        else:
            lang = self.user_lang
            country = self.user_country

        splatnet3_url = "https://api.lp1.av5ja.srv.nintendo.net"

        graphql_head = {
            "Authorization": f"Bearer {self.bullet_token}",
            "Accept-Language": lang,
            "User-Agent": APP_USER_AGENT,
            "X-Web-View-Ver": NSOAuth.get_web_view_ver(),
            "Content-Type": "application/json",
            "Accept": "*/*",
            "Origin": splatnet3_url,
            "X-Requested-With": "com.nintendo.znca",
            "Referer": f"{splatnet3_url}/?lang={lang}&na_country={country}&na_lang={lang}",
            "Accept-Encoding": "gzip, deflate",
        }
        return graphql_head

    @_request_lock
    async def request(
        self,
        data: str,
        force_lang: Optional[str] = None,
        force_country: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        发送 GraphQL 请求（参照 Splatoon.request()）

        增强功能：
        - 自动处理 401 错误并刷新 token
        - 最多重试 1 次（避免死循环）
        - 支持并发请求的刷新锁

        Args:
            data: GraphQL 请求体
            force_lang: 强制语言
            force_country: 强制国家

        Returns:
            API 响应 JSON 或 None

        Raises:
            SessionExpiredError: session_token 过期，需要重新登录
            MembershipRequiredError: NSO 会员过期
            BulletTokenError: Bullet token 获取失败（版本过时/封禁等）
            TokenRefreshError: Token 刷新失败
        """
        client = self._get_client()

        # 首次尝试
        try:
            headers = self.head_bullet(force_lang, force_country)
            cookies = {"_gtoken": self.g_token}

            resp = await client.post(
                GRAPHQL_URL,
                data=data,
                headers=headers,
                cookies=cookies,
            )

            # 检查 401（token 过期）
            if resp.status_code == 401:
                # 如果不支持自动刷新，直接返回 None
                if not self._can_auto_refresh():
                    logger.warning("401 错误，但无法自动刷新（缺少认证信息）")
                    return None

                logger.info("检测到 401 错误，开始刷新 tokens...")

                # 刷新 token（可能抛出异常）
                success, token_data = await self._refresh_tokens()

                # 刷新成功后立即回调持久化，不依赖重试结果
                if self.on_tokens_updated and token_data:
                    try:
                        if asyncio.iscoroutinefunction(self.on_tokens_updated):
                            await self.on_tokens_updated(token_data)
                        else:
                            self.on_tokens_updated(token_data)
                    except Exception as e:
                        logger.error(f"Token 回调失败: {e}")

                # 重试请求（只重试一次）
                logger.info("Tokens 刷新完成，重试请求...")
                headers = self.head_bullet(force_lang, force_country)
                cookies = {"_gtoken": self.g_token}

                resp = await client.post(
                    GRAPHQL_URL,
                    data=data,
                    headers=headers,
                    cookies=cookies,
                )

                if resp.status_code != 200:
                    logger.warning(f"重试后仍失败，状态码: {resp.status_code}")
                    return None

            elif resp.status_code != 200:
                logger.warning(f"请求失败，状态码: {resp.status_code}")
                return None

            return resp.json()

        except (SessionExpiredError, MembershipRequiredError, BulletTokenError):
            # 明确的认证/token 错误，向上抛出
            raise
        except TokenRefreshError as e:
            # Token 刷新失败，向上抛出以便调用者知道具体原因
            logger.error(f"Token 刷新失败: {e}")
            raise
        except Exception as e:
            logger.error(f"请求错误: {e}")
            return None

    async def test_connection(self) -> bool:
        """
        测试连接并自动刷新 token（参照 splatoon3-nso 的 test_page）

        Returns:
            连接是否成功
        """
        try:
            result = await self.get_home()
            return result is not None
        except (SessionExpiredError, MembershipRequiredError):
            # 认证错误不算连接失败，向上抛出
            raise
        except Exception:
            return False

    def head_access(self, app_access_token):
        """为含有access_token的请求拼装header"""
        coral_head = {
            'User-Agent': f'com.nintendo.znca/{NSOAuth.get_nsoapp_version()} (Android/12)',
            'Accept-Encoding': 'gzip',
            'Connection': 'Keep-Alive',
            'Host': 'api-lp1.znc.srv.nintendo.net',
            'X-ProductVersion': NSOAuth.get_nsoapp_version(),
            "Content-Type": "application/octet-stream",
            "Accept": "application/octet-stream, application/json",
            'Authorization': f"Bearer {app_access_token}",
            'X-Platform': 'Android',
            'Pragma': 'no-cache',
            'Cache-Control': 'no-cache',
        }
        return coral_head

    @_request_lock
    async def ns_request(
        self,
        url: str,
    ) -> Optional[Dict[str, Any]]:
        """
        发送 nso层面操作请求（参照 Splatoon._ns_api_request()）

        Args:
            url: 接口地址

        Returns:
            API 响应 JSON 或 None
        """
        client = self._get_client()

        # 首次尝试
        try:
            headers = self.head_access(self.access_token)
            json_body = {'parameter': {}}
            auth = NSOAuth()
            encrypt_request = await auth.f_encrypt_request(api_url=url, body_data=json_body,
                                                           access_token=self.access_token)
            encrypt_json = encrypt_request.json()
            encrypt_data = encrypt_json['data']
            body_bytes = base64.b64decode(encrypt_data)

            encrypt_resp = await client.post(
                url,
                data=body_bytes,
                headers=headers,
            )
            # 解密响应
            decrypt_resp = await auth.f_decrypt_response(encrypt_resp.content)
            decrypt_json = decrypt_resp.json()

            if decrypt_resp.status_code != 200:
                logger.warning(f"请求失败，状态码: {decrypt_resp.status_code}")
                return None

            return decrypt_json['data']
        except Exception as e:
            logger.error(f"请求错误: {e}")
            return None

    # ============================================================
    # 对战查询方法 (参照 Splatoon class)
    # ============================================================

    async def get_recent_battles(self) -> Optional[Dict[str, Any]]:
        """最近对战查询"""
        data = gen_graphql_body("LatestBattleHistoriesQuery")
        return await self.request(data)

    async def get_regular_battles(self) -> Optional[Dict[str, Any]]:
        """涂地对战查询"""
        data = gen_graphql_body("RegularBattleHistoriesQuery")
        return await self.request(data)

    async def get_bankara_battles(self) -> Optional[Dict[str, Any]]:
        """蛮颓对战查询"""
        data = gen_graphql_body("BankaraBattleHistoriesQuery")
        return await self.request(data)

    async def get_x_battles(self) -> Optional[Dict[str, Any]]:
        """X对战查询"""
        data = gen_graphql_body("XBattleHistoriesQuery")
        return await self.request(data)

    async def get_event_battles(self) -> Optional[Dict[str, Any]]:
        """活动对战查询"""
        data = gen_graphql_body("EventBattleHistoriesQuery")
        return await self.request(data)

    async def get_private_battles(self) -> Optional[Dict[str, Any]]:
        """私房对战查询"""
        data = gen_graphql_body("PrivateBattleHistoriesQuery")
        return await self.request(data)

    async def get_battle_detail(self, battle_id: str) -> Optional[Dict[str, Any]]:
        """对战详情查询"""
        data = gen_graphql_body("VsHistoryDetailQuery", "vsResultId", battle_id)
        return await self.request(data)

    async def get_last_one_battle(self) -> Optional[Dict[str, Any]]:
        """最新一局对战id查询"""
        data = gen_graphql_body("PagerLatestVsDetailQuery")
        return await self.request(data)

    # ============================================================
    # 打工查询方法
    # ============================================================

    async def get_coops(self) -> Optional[Dict[str, Any]]:
        """打工历史查询"""
        data = gen_graphql_body("CoopHistoryQuery")
        return await self.request(data)

    async def get_coop_detail(self, coop_id: str) -> Optional[Dict[str, Any]]:
        """打工详情查询"""
        data = gen_graphql_body("CoopHistoryDetailQuery", "coopHistoryDetailId", coop_id)
        return await self.request(data)

    # ============================================================
    # 排名和其他查询
    # ============================================================

    async def get_x_ranking(self, region: str = "ATLANTIC") -> Optional[Dict[str, Any]]:
        """X排行榜top1查询"""
        data = gen_graphql_body("XRankingQuery", "region", region)
        return await self.request(data)

    async def get_home(self) -> Optional[Dict[str, Any]]:
        """主页数据查询"""
        data = gen_graphql_body("HomeQuery", "naCountry", "JP")
        return await self.request(data)

    async def get_history_summary(self) -> Optional[Dict[str, Any]]:
        """历史总览查询"""
        data = gen_graphql_body("HistoryRecordQuery")
        return await self.request(data)

    async def get_friends(self) -> Optional[Dict[str, Any]]:
        """好友列表查询"""
        data = gen_graphql_body("FriendListQuery")
        return await self.request(data)

    async def get_weapon_records(self) -> Optional[Dict[str, Any]]:
        """武器记录查询"""
        data = gen_graphql_body("WeaponRecordQuery")
        return await self.request(data)

    async def get_stage_records(self) -> Optional[Dict[str, Any]]:
        """场地记录查询"""
        data = gen_graphql_body("StageRecordQuery")
        return await self.request(data)

    async def get_schedule(self) -> Optional[Dict[str, Any]]:
        """日程表查询"""
        data = gen_graphql_body("StageScheduleQuery")
        return await self.request(data)

    async def close(self) -> None:
        """关闭 HTTP client 和 NSOAuth"""
        if self._client:
            await self._client.close()
            self._client = None
        if self.nso_auth:
            await self.nso_auth.close() # TODO: 这里没有close方法

    # ============================================================
    # nso app查询
    # ============================================================

    async def get_app_ns_friend_list(self) -> Optional[Dict[str, Any]]:
        """nso app 好友列表"""
        url = "https://api-lp1.znc.srv.nintendo.net/v4/Friend/List"
        return await self.ns_request(url)

    async def get_app_ns_myself(self) -> Optional[Dict[str, Any]]:
        """nso app 我的信息"""
        url = "https://api-lp1.znc.srv.nintendo.net/v4/User/ShowSelf"
        return await self.ns_request(url)