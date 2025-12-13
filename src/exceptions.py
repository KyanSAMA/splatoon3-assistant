# Custom exceptions for splatoon3-assistant
"""
定义明确的异常类型，便于错误处理和用户友好的提示
"""


class SplatoonError(Exception):
    """基础异常类"""
    pass


class SessionExpiredError(SplatoonError):
    """
    Session Token 过期错误

    当 session_token 失效时抛出，通常是因为：
    - 密码被修改
    - Token 被撤销
    - Token 过期（一般为 2 年）

    处理方式：需要用户重新登录（扫码获取新的 session_token）
    """
    pass


class MembershipRequiredError(SplatoonError):
    """
    NSO 会员过期错误

    当 Nintendo Switch Online 会员过期时抛出

    处理方式：提示用户续费 NSO 会员
    """
    def __init__(self, nickname: str = ""):
        self.nickname = nickname
        message = f"Nintendo Switch Online 会员已过期"
        if nickname:
            message = f"账号 {nickname} 的 " + message
        super().__init__(message)


class BulletTokenError(SplatoonError):
    """
    Bullet Token 相关错误

    包括：
    - 401: 无效的 game web token
    - 403: 版本过时
    - 204: 用户未注册
    - 499: 用户被封禁
    """
    def __init__(self, status_code: int, message: str = ""):
        self.status_code = status_code
        if not message:
            if status_code == 401:
                message = "无效的 Game Web Token"
            elif status_code == 403:
                message = "应用版本过时，请更新"
            elif status_code == 204:
                message = "用户未在 SplatNet3 注册"
            elif status_code == 499:
                message = "用户已被封禁"
            else:
                message = f"Bullet Token 错误 (状态码: {status_code})"
        super().__init__(message)


class NetworkError(SplatoonError):
    """
    网络连接错误

    包括：
    - 连接超时
    - 连接失败
    - DNS 解析失败

    处理方式：可以重试
    """
    pass


class TokenRefreshError(SplatoonError):
    """
    Token 刷新失败错误

    当自动刷新 token 失败时抛出（非 session 过期或会员过期）

    处理方式：可以重试，或提示用户检查网络
    """
    pass
