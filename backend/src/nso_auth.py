# NSO OAuth Authentication module
# Based on reference-project/splatoon3-nso/s3s/iksm.py (S3S class)
"""Nintendo Switch Online OAuth authentication flow."""

import base64
import hashlib
import json
import os
import re
import urllib.parse
from typing import Optional, Tuple, Dict, Any

import httpx
from bs4 import BeautifulSoup

from .config import Config, default_config
from .http_client import HttpClient, AsyncHttpClient
from .exceptions import SessionExpiredError, MembershipRequiredError, BulletTokenError


# Constants
F_GEN_URL = "https://nxapi-znca-api.fancy.org.uk/api/znca/f"
F_GEN_OAUTH_URL = "https://nxapi-auth.fancy.org.uk/api/oauth/token"
F_GEN_OAUTH_CLIENT_ID = "EJ5mqnRSwmWfOPmRDIRGwg" 

# Version (globals like in splatoon3-nso)
NSOAPP_VERSION = "unknown"
NSOAPP_VER_FALLBACK = "3.2.0"
WEB_VIEW_VERSION = "unknown"
WEB_VIEW_VER_FALLBACK = "10.0.0-cba84fcd"
ZNCA_CLIENT_VERSION = "unknown"  # 3.1.0+ 由 nxapi-auth 签发的随机客户端版本
ZNCA_CLIENT_VER_FALLBACK = "hio87-mJks_e9GNF"  # 兼容旧协议的静态版本

# User agents
APP_USER_AGENT = (
    "Mozilla/5.0 (Linux; Android 14; Pixel 7a) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.6099.230 Mobile Safari/537.36"
)
F_USER_AGENT = f"splatoon3_assistant/0.1.1"


class NSOAuth:
    """
    Nintendo Switch Online OAuth authentication (参照 splatoon3-nso S3S class)
    
    Usage:
        auth = NSOAuth()
        url, verifier = await auth.login_in()
        session_token = await auth.login_in_2(callback_url, verifier)
        access_token, g_token, nickname, lang, country, user_info = await auth.get_gtoken(session_token)
        bullet_token = await auth.get_bullet(g_token)
    """
    
    def __init__(self, config: Optional[Config] = None):
        self.config = config or default_config
        self.async_client: Optional[AsyncHttpClient] = None
        self.oauth_token: Optional[str] = None
        
        self.user_lang = "zh-CN"
        self.user_country = "JP"
        self.user_nickname = ""
        self.r_user_id = ""
    
    def _get_async_client(self) -> AsyncHttpClient:
        """Get or create async HTTP client."""
        if self.async_client is None:
            self.async_client = AsyncHttpClient(self.config)
        return self.async_client
    
    @staticmethod
    def get_nsoapp_version(f_gen_url: str = F_GEN_URL) -> str:
        """获取 NSO app 版本（参照 splatoon3-nso）"""
        global NSOAPP_VERSION
        if NSOAPP_VERSION != "unknown":
            return NSOAPP_VERSION

        # 允许通过环境变量手动覆盖（便于在远端不可用时指定最新版本）
        env_ver = os.environ.get("SPLATOON3_NSOAPP_VERSION")
        if env_ver:
            NSOAPP_VERSION = env_ver
            return NSOAPP_VERSION

        try:
            # Try f-API config endpoint
            f_conf_url = f_gen_url.replace("/f", "") + "/config"
            f_conf_header = {"User-Agent": F_USER_AGENT}

            with httpx.Client() as client:
                resp = client.get(f_conf_url, headers=f_conf_header, timeout=10)
                data = resp.json()
                ver = data.get("nso_version")
                if ver:
                    NSOAPP_VERSION = ver
                    return NSOAPP_VERSION
        except Exception as e:
            print(f"[warn] Failed to fetch nso_version from f-config: {e}")

        try:
            # Fallback: Apple App Store
            with httpx.Client() as client:
                page = client.get(
                    "https://apps.apple.com/us/app/nintendo-switch-online/id1234806557",
                    timeout=10
                )
                soup = BeautifulSoup(page.text, "html.parser")
                elt = soup.find("p", {"class": "whats-new__latest__version"})
                if elt:
                    ver = elt.get_text().replace("Version ", "").strip()
                    NSOAPP_VERSION = ver
                    return NSOAPP_VERSION
        except Exception as e:
            print(f"[warn] Failed to fetch nso_version from App Store: {e}")

        # 最后回退到硬编码版本，确保不可用时仍有值，但提醒更新
        print(f"[warn] Falling back to NSOAPP_VER_FALLBACK={NSOAPP_VER_FALLBACK}")
        NSOAPP_VERSION = NSOAPP_VER_FALLBACK
        return NSOAPP_VERSION
    
    @staticmethod
    def get_web_view_ver() -> str:
        """获取 Web View 版本(参照 splatoon3-nso)"""
        global WEB_VIEW_VERSION
        if WEB_VIEW_VERSION != "unknown":
            return WEB_VIEW_VERSION

        return WEB_VIEW_VER_FALLBACK

    @staticmethod
    def get_znca_client_version() -> str:
        """
        获取 X-znca-Client-Version。

        3.1.0+ 按官方说明应使用 nxapi-auth 签发的随机客户端版本，不应随 NSO 应用版本变化。
        若未能从远端获得，则允许通过环境变量覆盖，最后回退到兼容的静态版本。

        Returns:
            X-znca-Client-Version 的值
        """
        global ZNCA_CLIENT_VERSION
        if ZNCA_CLIENT_VERSION != "unknown":
            return ZNCA_CLIENT_VERSION

        # 支持通过环境变量注入（便于外部获取后传入）
        env_ver = os.environ.get("SPLATOON3_ZNCA_CLIENT_VERSION")
        if env_ver:
            ZNCA_CLIENT_VERSION = env_ver
            return ZNCA_CLIENT_VERSION

        return ZNCA_CLIENT_VER_FALLBACK

    @staticmethod
    def reset_cached_versions() -> None:
        """重置缓存的版本号"""
        global NSOAPP_VERSION, WEB_VIEW_VERSION, ZNCA_CLIENT_VERSION
        NSOAPP_VERSION = "unknown"
        WEB_VIEW_VERSION = "unknown"
        ZNCA_CLIENT_VERSION = "unknown"
    
    async def login_in(self) -> Tuple[str, bytes]:
        """
        登录步骤第一步：生成登录 URL（参照 s3s.login_in()）
        
        Returns:
            Tuple of (login_url, auth_code_verifier)
        """
        auth_state = base64.urlsafe_b64encode(os.urandom(36))
        auth_code_verifier = base64.urlsafe_b64encode(os.urandom(32))
        
        auth_cv_hash = hashlib.sha256()
        auth_cv_hash.update(auth_code_verifier.replace(b"=", b""))
        auth_code_challenge = base64.urlsafe_b64encode(auth_cv_hash.digest())
        
        body = {
            "state": auth_state.decode("utf-8"),
            "redirect_uri": "npf71b963c1b7b6d119://auth",
            "client_id": "71b963c1b7b6d119",
            "scope": "openid user user.birthday user.mii user.screenName",
            "response_type": "session_token_code",
            "session_token_code_challenge": auth_code_challenge.replace(b"=", b"").decode("utf-8"),
            "session_token_code_challenge_method": "S256",
            "theme": "login_form",
        }
        
        url = f"https://accounts.nintendo.com/connect/1.0.0/authorize?{urllib.parse.urlencode(body)}"
        
        return url, auth_code_verifier
    
    async def login_in_2(self, use_account_url: str, auth_code_verifier: bytes) -> Optional[str]:
        """
        登录步骤第二步：获取 session_token（参照 s3s.login_in_2()）
        
        Args:
            use_account_url: 回调 URL (npf...)
            auth_code_verifier: login_in() 返回的验证码
            
        Returns:
            session_token or None
        """
        try:
            if use_account_url == "skip":
                return None
            
            match = re.search(r"de=(.*)&st", use_account_url)
            if not match:
                return None
            
            session_token_code = match.group(1)
            resp = await self._get_session_token(session_token_code, auth_code_verifier)
            session_token = resp.get("session_token")
            return session_token
            
        except Exception as e:
            print(f"login_in_2 error: {e}")
            return None
    
    async def _get_session_token(
        self,
        session_token_code: str,
        auth_code_verifier: bytes
    ) -> Dict[str, Any]:
        """获取 session_token（参照 S3S.get_session_token()）"""
        nsoapp_version = self.get_nsoapp_version()
        
        app_head = {
            "User-Agent": f"OnlineLounge/{nsoapp_version} NASDKAPI Android",
            "Accept-Language": "en-US",
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded",
            "Host": "accounts.nintendo.com",
            "Connection": "Keep-Alive",
            "Accept-Encoding": "gzip",
        }
        
        body = {
            "client_id": "71b963c1b7b6d119",
            "session_token_code": session_token_code,
            "session_token_code_verifier": auth_code_verifier.replace(b"=", b"").decode("utf-8"),
        }
        
        client = self._get_async_client()
        resp = await client.post(
            "https://accounts.nintendo.com/connect/1.0.0/api/session_token",
            headers=app_head,
            data=body,
        )
        return resp.json()
    
    async def get_gtoken(self, session_token: str) -> Tuple[str, str, str, str, str, Dict[str, Any]]:
        """
        获取 g_token（参照 S3S.get_gtoken()系列方法）
        
        Returns:
            (access_token, g_token, nickname, lang, country, current_user)
        """
        #Step 1: Get ID token
        id_token, user_info = await self._get_id_token_and_user_info(session_token)
        
        if not id_token or not user_info:
            raise ValueError("Failed to get id_token or user_info")
        
        # Step 2: Get access token
        access_token, f, uuid, timestamp, coral_user_id, current_user = await self._get_access_token(
            id_token, user_info
        )
        
        # Step 3: Get g_token
        g_token = await self._get_g_token(access_token, coral_user_id)

        return access_token, g_token, self.user_nickname, self.user_lang, self.user_country, current_user
    
    async def _get_id_token_and_user_info(
        self,
        session_token: str
    ) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
        """get_gtoken 第一步（参照 S3S._get_id_token_and_user_info()）"""
        client = self._get_async_client()
        
        app_head = {
            "Host": "accounts.nintendo.com",
            "Accept-Encoding": "gzip",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Connection": "Keep-Alive",
            "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 14; Pixel 7a Build/UQ1A.240105.004)",
        }
        body = {
            "client_id": "71b963c1b7b6d119",
            "session_token": session_token,
            "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer-session-token",
        }
        
        resp = await client.post(
            "https://accounts.nintendo.com/connect/1.0.0/api/token",
            headers=app_head,
            json=body,
        )
        id_response = resp.json()

        if id_response.get("error") == "invalid_grant":
            raise SessionExpiredError("Session token 已过期或失效，请重新登录")
        
        id_access_token = id_response.get("access_token")
        id_token = id_response.get("id_token")
        
        if not id_access_token:
            return None, None
        
        # Get user info
        app_head = {
            "User-Agent": "NASDKAPI; Android",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {id_access_token}",
            "Host": "api.accounts.nintendo.com",
            "Connection": "Keep-Alive",
            "Accept-Encoding": "gzip",
        }
        
        resp = await client.get(
            "https://api.accounts.nintendo.com/2.0.0/users/me",
            headers=app_head,
        )
        user_info = resp.json()
        
        return id_token, user_info
    
    async def _get_access_token(
        self,
        id_token: str,
        user_info: Dict[str, Any]
    ) -> Tuple[str, str, str, int, str, Dict[str, Any]]:
        """get_gtoken 第二步（参照 S3S._get_access_token()）"""
        self.user_nickname = user_info["nickname"]
        self.user_lang = user_info["language"]
        self.user_country = user_info["country"]
        self.r_user_id = user_info["id"]
        birthday = user_info["birthday"]

        # 准备 parameter 用于加密请求
        parameter = {
            "f": "",  # 将由 f-API 填充
            "language": self.user_lang,
            "naBirthday": birthday,
            "naCountry": self.user_country,
            "naIdToken": id_token,
            "requestId": "",  # 将由 f-API 填充
            "timestamp": 0,  # 将由 f-API 填充
        }

        # 调用 f-API 并请求加密数据
        enc_req = {
            "url": "https://api-lp1.znc.srv.nintendo.net/v4/Account/Login",
            "parameter": parameter,
        }
        f, uuid, timestamp, enc_payload = await self.call_f_api(
            id_token, 1, self.r_user_id, encrypt_token_request=enc_req
        )

        # 更新 parameter
        parameter["f"] = f
        parameter["requestId"] = uuid
        parameter["timestamp"] = timestamp

        nsoapp_version = self.get_nsoapp_version()
        znca_client_version = self.get_znca_client_version()

        client = self._get_async_client()
        url = "https://api-lp1.znc.srv.nintendo.net/v4/Account/Login"

        # 根据是否有加密载荷决定请求模式
        if enc_payload:
            # 加密模式：base64 解码后发送二进制数据
            print("[DEBUG] Using encrypted request mode")
            body_bytes = base64.b64decode(enc_payload)

            app_head = {
                "X-Platform": "Android",
                "X-ProductVersion": nsoapp_version,
                "X-znca-Client-Version": znca_client_version,
                "Content-Type": "application/octet-stream",
                "Accept": "application/octet-stream, application/json",
                "Connection": "Keep-Alive",
                "Accept-Encoding": "gzip",
                "User-Agent": f"com.nintendo.znca/{nsoapp_version}(Android/14)",
            }

            resp = await client.post(url, headers=app_head, content=body_bytes)

            # 解密响应
            decrypt_resp = await self.f_decrypt_response(resp.content)
            decrypt_json = decrypt_resp.json()
            splatoon_token = json.loads(decrypt_json["data"])
        else:
            # v4 API 强制加密，若未获取到加密载荷则为异常
            raise ValueError(
                "Failed to get encrypted payload from f-API. "
                "v4 API requires encryption. Check OAuth client_id and scope."
            )

        try:
            access_token = splatoon_token["result"]["webApiServerCredential"]["accessToken"]
            coral_user_id = splatoon_token["result"]["user"]["id"]
            current_user = splatoon_token["result"]["user"]
        except (KeyError, TypeError):
            # Retry once (参照 splatoon3-nso retry logic for 9403/9599/9427)
            try:
                print(f"[DEBUG] First attempt failed ({splatoon_token.get('status')}), retrying...")

                # 重新生成 f
                enc_req["parameter"] = parameter
                f, uuid, timestamp, enc_payload = await self.call_f_api(
                    id_token, 1, self.r_user_id, encrypt_token_request=enc_req
                )
                parameter["f"] = f
                parameter["requestId"] = uuid
                parameter["timestamp"] = timestamp

                # 准备重试请求
                if enc_payload:
                    body_bytes = base64.b64decode(enc_payload)
                    resp = await client.post(url, headers=app_head, content=body_bytes)
                    decrypt_resp = await self.f_decrypt_response(resp.content)
                    decrypt_json = decrypt_resp.json()
                    splatoon_token = json.loads(decrypt_json["data"])
                else:
                    raise ValueError("Failed to get encrypted payload from f-API on retry")

                access_token = splatoon_token["result"]["webApiServerCredential"]["accessToken"]
                coral_user_id = splatoon_token["result"]["user"]["id"]
                current_user = splatoon_token["result"]["user"]
            except json.JSONDecodeError:
                raise ValueError("JSONDecodeError")
            except Exception:
                raise ValueError(f"Failed to get access_token: {splatoon_token}")

        # Get f for step 2 (不再需要这一步，在 _get_g_token 中调用)
        return access_token, f, uuid, timestamp, coral_user_id, current_user
    
    async def _get_g_token(
        self,
        access_token: str,
        coral_user_id: str,
    ) -> str:
        """
        get_gtoken 第三步（参照 S3S._get_g_token()）

        注意：此方法会调用 f-API 重新生成 f/uuid/timestamp，不复用 step 1 的值
        """
        nsoapp_version = self.get_nsoapp_version()
        znca_client_version = self.get_znca_client_version()

        # 准备 parameter
        parameter = {
            "f": "",  # 将由 f-API 填充
            "id": 4834290508791808,
            "registrationToken": access_token,
            "requestId": "",  # 将由 f-API 填充
            "timestamp": 0,  # 将由 f-API 填充
        }

        url = "https://api-lp1.znc.srv.nintendo.net/v4/Game/GetWebServiceToken"

        # 调用 f-API 并请求加密数据
        enc_req = {
            "url": url,
            "parameter": parameter,
        }
        f, uuid, timestamp, enc_payload = await self.call_f_api(
            access_token, 2, self.r_user_id, coral_user_id, encrypt_token_request=enc_req
        )

        # 更新 parameter
        parameter["f"] = f
        parameter["requestId"] = uuid
        parameter["timestamp"] = timestamp

        client = self._get_async_client()

        # 根据是否有加密载荷决定请求模式
        if enc_payload:
            # 加密模式
            print("[DEBUG] Using encrypted request mode for g_token")
            body_bytes = base64.b64decode(enc_payload)

            app_head = {
                "X-Platform": "Android",
                "X-ProductVersion": nsoapp_version,
                "X-znca-Client-Version": znca_client_version,
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/octet-stream",
                "Accept": "application/octet-stream, application/json",
                "Accept-Encoding": "gzip",
                "User-Agent": f"com.nintendo.znca/{nsoapp_version}(Android/14)",
            }

            resp = await client.post(url, headers=app_head, content=body_bytes)

            # 解密响应
            decrypt_resp = await self.f_decrypt_response(resp.content)
            decrypt_json = decrypt_resp.json()
            web_service_resp = json.loads(decrypt_json["data"])
        else:
            # v4 API 强制加密，若未获取到加密载荷则为异常
            raise ValueError(
                "Failed to get encrypted payload from f-API for g_token. "
                "v4 API requires encryption. Check OAuth client_id and scope."
            )

        try:
            return web_service_resp["result"]["accessToken"]
        except (KeyError, TypeError):
            error_msg = web_service_resp.get("errorMessage", "Unknown error")
            nickname = self.user_nickname or ""
            if error_msg == "Membership required error.":
                raise MembershipRequiredError(nickname)
            raise ValueError(f"Failed to get g_token: {web_service_resp}")
    
    async def get_bullet(self, g_token: str) -> Optional[str]:
        """
        获取 bullet_token（参照 S3S.get_bullet()）
        
        Args:
            g_token: GameWebToken
            
        Returns:
            bullet_token or None
        """
        splatnet_url = "https://api.lp1.av5ja.srv.nintendo.net"
        
        app_head = {
            "Content-Length": "0",
            "Content-Type": "application/json",
            "Accept-Language": self.user_lang,
            "User-Agent": APP_USER_AGENT,
            "X-Web-View-Ver": self.get_web_view_ver(),
            "X-NACOUNTRY": self.user_country,
            "Accept": "*/*",
            "Origin": splatnet_url,
            "X-Requested-With": "com.nintendo.znca",
        }
        app_cookies = {
            "_gtoken": g_token,
            "_dnt": "1",
        }
        
        client = self._get_async_client()
        resp = await client.post(
            f"{splatnet_url}/api/bullet_tokens",
            headers=app_head,
            cookies=app_cookies,
        )
        
        if resp.status_code == 401:
            raise BulletTokenError(401, "无效的 Game Web Token")
        elif resp.status_code == 403:
            raise BulletTokenError(403, "应用版本过时")
        elif resp.status_code == 204:
            raise BulletTokenError(204, "用户未在 SplatNet3 注册")
        elif resp.status_code == 499:
            raise BulletTokenError(499, "用户已被封禁")
        
        try:
            return resp.json().get("bulletToken")
        except Exception:
            return None
    
    async def f_api_client_auth2_register(self) -> None:
        """注册 f-API OAuth token（参照 S3S.f_api_clent_auth2_register()）"""
        api_head = {
            "User-Agent": F_USER_AGENT,
            "Content-Type": "application/x-www-form-urlencoded",
        }
        api_body = {
            "grant_type": "client_credentials",
            "client_id": F_GEN_OAUTH_CLIENT_ID,
            "scope": "ca:gf ca:er ca:dr",  # 添加 ca:er ca:dr scope 用于加密/解密
        }

        client = self._get_async_client()
        resp = await client.post(F_GEN_OAUTH_URL, headers=api_head, data=api_body)
        data = resp.json()
        self.oauth_token = data.get("access_token")

        if self.oauth_token:
            print(f"[DEBUG] ✅ OAuth token received: {self.oauth_token[:20]}...")
        else:
            print(f"[DEBUG] ❌ No access_token in response!")
            if "error" in data:
                print(f"[DEBUG] OAuth Error: {data.get('error')}")
                print(f"[DEBUG] Error description: {data.get('error_description')}")

        # 捕获 nxapi-auth 返回的客户端版本（若提供），满足 3.1.0+ 的随机版本要求
        client_ver = data.get("client_version") or data.get("znca_client_version")
        if client_ver:
            print(f"[DEBUG] Client version from OAuth: {client_ver}")
            global ZNCA_CLIENT_VERSION
            ZNCA_CLIENT_VERSION = client_ver
    
    async def call_f_api(
        self,
        access_token: str,
        step: int,
        r_user_id: str,
        coral_user_id: Optional[str] = None,
        encrypt_token_request: Optional[Dict[str, Any]] = None,
    ) -> Tuple[str, str, int, Optional[str]]:
        """
        调用 f-API（参照 S3S.call_f_api()）

        Args:
            access_token: NSO access token or ID token
            step: 1 for coral token, 2 for web service token
            r_user_id: Nintendo account user ID
            coral_user_id: Coral user ID (step 2 需要)
            encrypt_token_request: 可选的加密请求信息 (url + parameter)

        Returns:
            (f_token, uuid, timestamp, encrypted_payload_base64_or_none)
        """
        if not self.oauth_token:
            await self.f_api_client_auth2_register()

        nsoapp_version = self.get_nsoapp_version()
        znca_client_version = self.get_znca_client_version()

        api_head = {
            "User-Agent": F_USER_AGENT,
            "Content-Type": "application/json; charset=utf-8",
            "X-znca-Platform": "Android",
            "X-znca-Version": nsoapp_version,
            "X-znca-Client-Version": znca_client_version,
            "Authorization": f"Bearer {self.oauth_token}",
        }

        api_body = {
            "token": access_token,
            "hash_method": step,
            "na_id": r_user_id,
        }

        if step == 2 and coral_user_id:
            api_body["coral_user_id"] = str(coral_user_id)

        if encrypt_token_request:
            api_body["encrypt_token_request"] = encrypt_token_request

        client = self._get_async_client()
        resp = await client.post(F_GEN_URL, headers=api_head, json=api_body)

        # Check status code
        if resp.status_code != 200:
            raise ValueError(f"f-API failed with status {resp.status_code}: {resp.text[:200]}")

        try:
            data = resp.json()
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse f-API response: {str(e)}, body: {resp.text[:200]}")

        # Handle token expiration
        if data.get("error") == "invalid_token":
            await self.f_api_client_auth2_register()
            api_head["Authorization"] = f"Bearer {self.oauth_token}"
            api_head["X-znca-Client-Version"] = self.get_znca_client_version()
            resp = await client.post(F_GEN_URL, headers=api_head, json=api_body)

            if resp.status_code != 200:
                raise ValueError(f"f-API retry failed with status {resp.status_code}: {resp.text[:200]}")

            try:
                data = resp.json()
            except json.JSONDecodeError as e:
                raise ValueError(f"Failed to parse f-API retry response: {str(e)}, body: {resp.text[:200]}")

        if "error" in data:
            raise ValueError(f"f-API error: {data}")

        print(f"[DEBUG] f-API response: {data}")
        # nxapi 若启用加密，会返回加密载荷（优先检查 encrypted_token_request）
        enc_payload = (
            data.get("encrypted_token_request")
            or data.get("encrypted")
            or data.get("encrypt_request")
            or data.get("request")
        )
        return data["f"], data["request_id"], data["timestamp"], enc_payload

    async def f_decrypt_response(self, encrypted_data: bytes) -> httpx.Response:
        """
        调用 nxapi /decrypt-response 解密加密响应（参照 S3S.f_decrypt_response()）

        Args:
            encrypted_data: 加密的响应数据（bytes）

        Returns:
            解密后的响应对象，其 .json() 返回 {"data": "..."}
        """
        if not self.oauth_token:
            await self.f_api_client_auth2_register()

        nsoapp_version = self.get_nsoapp_version()
        znca_client_version = self.get_znca_client_version()

        api_head = {
            "User-Agent": F_USER_AGENT,
            "Content-Type": "application/json; charset=utf-8",
            "Accept": "application/json; charset=utf-8",
            "X-znca-Platform": "Android",
            "X-znca-Version": nsoapp_version,
            "X-znca-Client-Version": znca_client_version,
            "Authorization": f"Bearer {self.oauth_token}",
        }

        api_body = {
            "data": base64.b64encode(encrypted_data).decode("utf-8"),
        }

        client = self._get_async_client()
        decrypt_url = F_GEN_URL.replace("/f", "/decrypt-response")

        resp = await client.post(decrypt_url, headers=api_head, json=api_body)

        # Handle token expiration
        if resp.status_code == 401:
            data = resp.json()
            if data.get("error") == "invalid_token":
                await self.f_api_client_auth2_register()
                api_head["Authorization"] = f"Bearer {self.oauth_token}"
                api_head["X-znca-Client-Version"] = self.get_znca_client_version()
                resp = await client.post(decrypt_url, headers=api_head, json=api_body)

        # Check for errors
        if resp.status_code != 200:
            raise ValueError(f"Decrypt failed with status {resp.status_code}: {resp.text[:200]}")

        try:
            data = resp.json()
            if "error" in data:
                raise ValueError(f"Decrypt error: {data}")
            if "data" not in data:
                raise ValueError(f"Decrypt response missing 'data' field: {data}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse decrypt response: {str(e)}, body: {resp.text[:200]}")

        return resp

    async def f_encrypt_request(self, api_url: str, access_token: str, body_data: dict) -> httpx.Response:

        """
        调用 nxapi /encrypt-request 加密请求，获取加密数据（参照 S3S.f_encrypt_token_request()）

        Args:
            api_url: 需要请求的路由地址
            access_token: nso token
            body_data: 参数body

        Returns:
            加密后的响应对象，其 .json() 返回 {"data": "..."}
        """
        if not self.oauth_token:
            await self.f_api_client_auth2_register()

        nsoapp_version = self.get_nsoapp_version()
        znca_client_version = self.get_znca_client_version()

        api_head = {
            "User-Agent": F_USER_AGENT,
            "Content-Type": "application/json; charset=utf-8",
            "Accept": "application/json; charset=utf-8",
            "X-znca-Platform": "Android",
            "X-znca-Version": nsoapp_version,
            "X-znca-Client-Version": znca_client_version,
            "Authorization": f"Bearer {self.oauth_token}",
        }

        api_body = {
            'url': api_url,
            'token': access_token,
            'data': json.dumps(body_data)
        }

        client = self._get_async_client()
        decrypt_url = F_GEN_URL.replace("/f", "/encrypt-request")

        resp = await client.post(decrypt_url, headers=api_head, json=api_body)

        # Handle token expiration
        if resp.status_code == 401:
            data = resp.json()
            if data.get("error") == "invalid_token":
                await self.f_api_client_auth2_register()
                api_head["Authorization"] = f"Bearer {self.oauth_token}"
                api_head["X-znca-Client-Version"] = self.get_znca_client_version()
                resp = await client.post(decrypt_url, headers=api_head, json=api_body)

        # Check for errors
        if resp.status_code != 200:
            raise ValueError(f"Encrypt failed with status {resp.status_code}: {resp.text[:200]}")

        try:
            data = resp.json()
            if "error" in data:
                raise ValueError(f"Encrypt error: {data}")
            if "data" not in data:
                raise ValueError(f"Encrypt response missing 'data' field: {data}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse encrypt response: {str(e)}, body: {resp.text[:200]}")

        return resp


    async def close(self) -> None:
        """关闭 async client"""
        if self.async_client:
            await self.async_client.close()
