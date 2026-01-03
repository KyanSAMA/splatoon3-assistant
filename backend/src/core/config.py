"""Configuration management for proxy settings and HTTP parameters."""

from typing import List, Optional

from .config_manager import ConfigManager


class Config:
    """HTTP 请求配置（代理、超时等）"""

    def __init__(self, manager: Optional[ConfigManager] = None):
        self._mgr = manager or ConfigManager.instance()
        self.user_agent = (
            "Mozilla/5.0 (Linux; Android 14; Pixel 7a) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.6099.230 Mobile Safari/537.36"
        )

    @property
    def proxy_address(self) -> Optional[str]:
        """代理地址"""
        addr = self._mgr.get_str("proxy.address", "")
        return addr if addr else None

    @property
    def proxy_enabled(self) -> bool:
        """是否启用代理"""
        return self._mgr.get_bool("proxy.enabled", True)

    @property
    def proxy_list(self) -> List[str]:
        """需要代理的主机列表"""
        return self._mgr.get_json("proxy.hosts", [])

    @property
    def http_timeout(self) -> float:
        """HTTP 超时秒数"""
        return self._mgr.get_float("http.timeout", 60.0)

    @property
    def proxies(self) -> Optional[str]:
        """格式化的代理 URL"""
        if self.proxy_enabled and self.proxy_address:
            return f"http://{self.proxy_address}"
        return None

    def should_use_proxy(self, host: str) -> bool:
        """检查是否应为该主机使用代理"""
        if not self.proxy_enabled or not self.proxy_address:
            return False
        hosts = self.proxy_list
        if not hosts:
            return True
        return host in hosts


# 全局默认配置实例
default_config = Config()
