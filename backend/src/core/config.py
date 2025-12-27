# Configuration module for Splatoon3 Assistant
"""Configuration management for proxy settings and HTTP parameters."""

import os
from typing import Optional, List


class Config:
    """Configuration for HTTP requests and proxy settings."""
    
    def __init__(
        self,
        proxy_address: Optional[str] = None,
        proxy_list_mode: bool = True,
        http_timeout: float = 60.0,
    ):
        self.proxy_address = proxy_address or os.environ.get("SPLATOON3_PROXY_ADDRESS")
        self.proxy_list_mode = proxy_list_mode
        self.http_timeout = float(os.environ.get("SPLATOON3_HTTP_TIMEOUT", http_timeout))
        
        # 需要使用代理的主机列表（参照 splatoon3-nso）
        self.proxy_list = [
            "accounts.nintendo.com",
            "api.accounts.nintendo.com",
            "api-lp1.znc.srv.nintendo.net",
            # "api.lp1.av5ja.srv.nintendo.net",
        ]
        
        self.user_agent = (
            "Mozilla/5.0 (Linux; Android 14; Pixel 7a) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.6099.230 Mobile Safari/537.36"
        )
    
    @property
    def proxies(self) -> Optional[str]:
        """Get formatted proxy URL."""
        if self.proxy_address:
            return f"http://{self.proxy_address}"
        return None
    
    def should_use_proxy(self, host: str) -> bool:
        """Check if should use proxy for given host."""
        if not self.proxy_address:
            return False
        
        if self.proxy_list_mode:
            return host in self.proxy_list
        else:
            return True


# Global default config instance
default_config = Config()
