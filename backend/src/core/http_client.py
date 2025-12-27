# HTTP client module for Splatoon3 Assistant
"""HTTP client wrappers with proxy support."""

import urllib.parse
from typing import Optional

import httpx

from .config import Config, default_config


class HttpClient:
    """Synchronous HTTP client with proxy support."""
    
    def __init__(self, config: Optional[Config] = None):
        self.config = config or default_config
    
    def _get_proxies(self, url: str) -> Optional[str]:
        """Get proxy for the given URL."""
        host = urllib.parse.urlparse(url).hostname
        if self.config.should_use_proxy(host):
            return self.config.proxies
        return None
    
    def get(self, url: str, **kwargs) -> httpx.Response:
        """Make a GET request."""
        proxies = self._get_proxies(url)
        timeout = kwargs.pop("timeout", self.config.http_timeout)
        
        with httpx.Client(proxy=proxies, http2=True) as client:
            return client.get(url, timeout=timeout, **kwargs)
    
    def post(self, url: str, **kwargs) -> httpx.Response:
        """Make a POST request."""
        proxies = self._get_proxies(url)
        timeout = kwargs.pop("timeout", self.config.http_timeout)
        
        with httpx.Client(proxy=proxies, http2=True) as client:
            return client.post(url, timeout=timeout, **kwargs)


class AsyncHttpClient:
    """Asynchronous HTTP client with proxy support."""
    
    def __init__(self, config: Optional[Config] = None, with_proxy: bool = False):
        self.config = config or default_config
        self.with_proxy = with_proxy
        self._client: Optional[httpx.AsyncClient] = None
        self._init_client()
    
    def _init_client(self) -> None:
        """Initialize async client."""
        proxy = self.config.proxies if self.with_proxy else None
        self._client = httpx.AsyncClient(
            proxy=proxy,
            http2=True,
            timeout=self.config.http_timeout,
        )
    
    def _should_use_temp_proxy(self, url: str) -> bool:
        """Check if should use temporary proxy client for this URL."""
        if self.with_proxy:
            return False
        host = urllib.parse.urlparse(url).hostname
        return self.config.should_use_proxy(host)
    
    async def _ensure_client_active(self) -> None:
        """Ensure client is active."""
        if self._client is None or self._client.is_closed:
            if self._client:
                try:
                    await self._client.aclose()
                except Exception:
                    pass
            self._init_client()
    
    async def get(self, url: str, **kwargs) -> httpx.Response:
        """Make an async GET request."""
        await self._ensure_client_active()
        
        if self._should_use_temp_proxy(url):
            async with httpx.AsyncClient(proxy=self.config.proxies, http2=True) as client:
                return await client.get(url, **kwargs)
        
        return await self._client.get(url, **kwargs)
    
    async def post(self, url: str, **kwargs) -> httpx.Response:
        """Make an async POST request."""
        await self._ensure_client_active()
        
        if self._should_use_temp_proxy(url):
            async with httpx.AsyncClient(proxy=self.config.proxies, http2=True) as client:
                return await client.post(url, **kwargs)
        
        return await self._client.post(url, **kwargs)
    
    async def close(self) -> None:
        """Close the async client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
