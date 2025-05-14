from typing import Any, Optional
from redis import Redis
from ..core.config import settings
import json

class RedisCache:
    def __init__(self):
        self.redis = Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            password=settings.REDIS_PASSWORD,
            decode_responses=True
        )
        self.default_ttl = 3600  # 1 hour default TTL
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        try:
            value = self.redis.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception:
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
            
        Returns:
            True if successful
        """
        try:
            ttl = ttl or self.default_ttl
            return self.redis.setex(
                key,
                ttl,
                json.dumps(value)
            )
        except Exception:
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete value from cache
        
        Args:
            key: Cache key
            
        Returns:
            True if successful
        """
        try:
            return bool(self.redis.delete(key))
        except Exception:
            return False
    
    async def clear(self) -> bool:
        """Clear all cached values
        
        Returns:
            True if successful
        """
        try:
            return bool(self.redis.flushdb())
        except Exception:
            return False