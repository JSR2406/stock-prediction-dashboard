"""
Caching Module - Redis-based caching with in-memory fallback.
"""

import json
import hashlib
from datetime import datetime, timedelta
from typing import Any, Callable, Optional, TypeVar
from functools import wraps
import asyncio

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

from app.config import settings
from app.utils.logging import logger

T = TypeVar('T')


class InMemoryCache:
    """Simple in-memory cache for development/fallback."""
    
    def __init__(self, default_ttl: int = 300):
        self._cache: dict = {}
        self._expiry: dict = {}
        self._lock = asyncio.Lock()
        self.default_ttl = default_ttl
    
    async def get(self, key: str) -> Optional[Any]:
        async with self._lock:
            if key not in self._cache:
                return None
            if datetime.utcnow() > self._expiry.get(key, datetime.min):
                del self._cache[key]
                del self._expiry[key]
                return None
            return self._cache[key]
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        async with self._lock:
            self._cache[key] = value
            self._expiry[key] = datetime.utcnow() + timedelta(seconds=ttl or self.default_ttl)
            return True
    
    async def delete(self, key: str) -> bool:
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
                del self._expiry[key]
                return True
            return False


class CacheManager:
    """Unified cache manager with Redis and In-Memory fallback."""
    
    def __init__(self):
        self.memory = InMemoryCache(default_ttl=settings.cache_ttl)
        self.redis: Optional[redis.Redis] = None
        self._redis_available = False
    
    async def initialize(self) -> None:
        """Initialize the cache connection."""
        if not REDIS_AVAILABLE:
            logger.warning("redis_not_installed", message="Redis library not found, using memory cache")
            return

        try:
            self.redis = redis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=2
            )
            # Test connection
            await self.redis.ping()
            self._redis_available = True
            logger.info("cache_initialized", backend="redis", host=settings.redis_host)
        except Exception as e:
            self._redis_available = False
            logger.warning("redis_connection_failed", error=str(e), message="Falling back to in-memory cache")
    
    async def get(self, key: str) -> Optional[Any]:
        if self._redis_available and self.redis:
            try:
                data = await self.redis.get(key)
                if data:
                    return json.loads(data)
            except Exception as e:
                logger.error("redis_get_error", key=key, error=str(e))
        
        return await self.memory.get(key)
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        ttl = ttl or settings.cache_ttl
        
        if self._redis_available and self.redis:
            try:
                await self.redis.set(
                    key, 
                    json.dumps(value), 
                    ex=ttl
                )
                return True
            except Exception as e:
                logger.error("redis_set_error", key=key, error=str(e))
        
        return await self.memory.set(key, value, ttl)
    
    async def delete(self, key: str) -> bool:
        if self._redis_available and self.redis:
            try:
                await self.redis.delete(key)
                return True
            except Exception as e:
                logger.error("redis_delete_error", key=key, error=str(e))
        
        return await self.memory.delete(key)
    
    def generate_key(self, prefix: str, *args, **kwargs) -> str:
        key_data = f"{prefix}:{':'.join(str(a) for a in args)}"
        if kwargs:
            key_data += f":{':'.join(f'{k}={v}' for k, v in sorted(kwargs.items()))}"
        if len(key_data) > 200:
            return f"{prefix}:{hashlib.md5(key_data.encode()).hexdigest()}"
        return key_data


cache_manager = CacheManager()


def cached(prefix: str, ttl: Optional[int] = None):
    """Caching decorator for async functions."""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            cache_key = cache_manager.generate_key(prefix, *args, **kwargs)
            cached_value = await cache_manager.get(cache_key)
            if cached_value is not None:
                return cached_value
            result = await func(*args, **kwargs)
            await cache_manager.set(cache_key, result, ttl)
            return result
        return wrapper
    decorator._is_cached = True # Mark for documentation/tracking
    return decorator
