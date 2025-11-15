"""
Caching infrastructure for Azure DevOps operations.

Implements TTL-based caching with automatic expiration and cache invalidation.
"""

import asyncio
import hashlib
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Optional, Dict, Callable
from functools import wraps

logger = logging.getLogger(__name__)


class CacheEntry:
    """
    Represents a cached value with TTL.

    Attributes:
        data: The cached data
        expiry: When this entry expires
        created_at: When this entry was created
        hit_count: Number of times this entry was retrieved
    """

    def __init__(self, data: Any, ttl_seconds: int):
        """
        Initialize cache entry.

        Args:
            data: The data to cache
            ttl_seconds: Time to live in seconds
        """
        self.data = data
        self.created_at = datetime.now()
        self.expiry = self.created_at + timedelta(seconds=ttl_seconds)
        self.hit_count = 0

    def is_expired(self) -> bool:
        """Check if this entry has expired."""
        return datetime.now() >= self.expiry

    def age_seconds(self) -> float:
        """Get age of this entry in seconds."""
        return (datetime.now() - self.created_at).total_seconds()

    def record_hit(self):
        """Record a cache hit."""
        self.hit_count += 1


class Cache:
    """
    Simple in-memory TTL-based cache.

    Features:
    - Automatic expiration based on TTL
    - Cache statistics (hits, misses, size)
    - Namespace support for organizing cache keys
    - Periodic cleanup of expired entries
    """

    def __init__(
        self,
        default_ttl_seconds: int = 300,
        max_size: int = 1000,
        cleanup_interval_seconds: int = 60
    ):
        """
        Initialize cache.

        Args:
            default_ttl_seconds: Default TTL for cache entries (default: 300 = 5 minutes)
            max_size: Maximum number of entries (default: 1000)
            cleanup_interval_seconds: How often to clean expired entries (default: 60)
        """
        self.default_ttl = default_ttl_seconds
        self.max_size = max_size
        self.cleanup_interval = cleanup_interval_seconds

        self._cache: Dict[str, CacheEntry] = {}
        self._stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'expirations': 0
        }

        # Start cleanup task
        self._cleanup_task: Optional[asyncio.Task] = None
        self._start_cleanup()

    def _start_cleanup(self):
        """Start periodic cleanup task."""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                self._cleanup_task = asyncio.create_task(self._periodic_cleanup())
        except RuntimeError:
            # No event loop, cleanup will be manual
            pass

    async def _periodic_cleanup(self):
        """Periodically clean expired entries."""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval)
                self.cleanup_expired()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cache cleanup: {e}")

    def cleanup_expired(self) -> int:
        """
        Remove expired entries from cache.

        Returns:
            Number of entries removed
        """
        before_count = len(self._cache)
        self._cache = {
            key: entry
            for key, entry in self._cache.items()
            if not entry.is_expired()
        }
        removed_count = before_count - len(self._cache)

        if removed_count > 0:
            self._stats['expirations'] += removed_count
            logger.debug(f"Cache cleanup: removed {removed_count} expired entries")

        return removed_count

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        entry = self._cache.get(key)

        if entry is None:
            self._stats['misses'] += 1
            return None

        if entry.is_expired():
            del self._cache[key]
            self._stats['expirations'] += 1
            self._stats['misses'] += 1
            return None

        entry.record_hit()
        self._stats['hits'] += 1

        logger.debug(
            f"Cache hit: {key} (age: {entry.age_seconds():.1f}s, "
            f"hits: {entry.hit_count})"
        )

        return entry.data

    def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: Optional[int] = None
    ):
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl_seconds: TTL for this entry (uses default if None)
        """
        # Check if we need to evict entries
        if len(self._cache) >= self.max_size and key not in self._cache:
            self._evict_oldest()

        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl
        self._cache[key] = CacheEntry(value, ttl)

        logger.debug(f"Cache set: {key} (TTL: {ttl}s)")

    def _evict_oldest(self):
        """Evict oldest entry to make room."""
        if not self._cache:
            return

        # Find oldest entry
        oldest_key = min(
            self._cache.keys(),
            key=lambda k: self._cache[k].created_at
        )

        del self._cache[oldest_key]
        self._stats['evictions'] += 1
        logger.debug(f"Cache eviction: {oldest_key}")

    def invalidate(self, key: str) -> bool:
        """
        Invalidate (remove) a cache entry.

        Args:
            key: Cache key to invalidate

        Returns:
            True if entry was removed, False if not found
        """
        if key in self._cache:
            del self._cache[key]
            logger.debug(f"Cache invalidation: {key}")
            return True
        return False

    def invalidate_prefix(self, prefix: str) -> int:
        """
        Invalidate all entries with keys starting with prefix.

        Args:
            prefix: Key prefix to match

        Returns:
            Number of entries invalidated
        """
        keys_to_remove = [
            key for key in self._cache.keys()
            if key.startswith(prefix)
        ]

        for key in keys_to_remove:
            del self._cache[key]

        if keys_to_remove:
            logger.debug(
                f"Cache invalidation: {len(keys_to_remove)} entries "
                f"with prefix '{prefix}'"
            )

        return len(keys_to_remove)

    def clear(self):
        """Clear all cache entries."""
        count = len(self._cache)
        self._cache.clear()
        logger.info(f"Cache cleared: {count} entries removed")

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        total_requests = self._stats['hits'] + self._stats['misses']
        hit_rate = (
            (self._stats['hits'] / total_requests * 100)
            if total_requests > 0
            else 0
        )

        return {
            'size': len(self._cache),
            'max_size': self.max_size,
            'hits': self._stats['hits'],
            'misses': self._stats['misses'],
            'hit_rate_percent': round(hit_rate, 2),
            'evictions': self._stats['evictions'],
            'expirations': self._stats['expirations'],
            'total_requests': total_requests
        }

    def __del__(self):
        """Cleanup on deletion."""
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()


# Global cache instance
_global_cache: Optional[Cache] = None


def get_cache(
    default_ttl_seconds: int = 300,
    max_size: int = 1000
) -> Cache:
    """
    Get or create global cache instance.

    Args:
        default_ttl_seconds: Default TTL (only used on first call)
        max_size: Maximum cache size (only used on first call)

    Returns:
        Global Cache instance
    """
    global _global_cache

    if _global_cache is None:
        _global_cache = Cache(
            default_ttl_seconds=default_ttl_seconds,
            max_size=max_size
        )

    return _global_cache


def make_cache_key(*args, **kwargs) -> str:
    """
    Generate cache key from function arguments.

    Args:
        *args: Positional arguments
        **kwargs: Keyword arguments

    Returns:
        Cache key string
    """
    # Serialize arguments to JSON
    key_data = {
        'args': args,
        'kwargs': sorted(kwargs.items())
    }

    key_json = json.dumps(key_data, sort_keys=True, default=str)

    # Hash for shorter keys
    key_hash = hashlib.sha256(key_json.encode()).hexdigest()[:16]

    return key_hash


def cached(
    ttl_seconds: Optional[int] = None,
    namespace: str = "",
    key_func: Optional[Callable] = None
):
    """
    Decorator to cache function results.

    Args:
        ttl_seconds: TTL for cached results (uses cache default if None)
        namespace: Namespace prefix for cache keys
        key_func: Custom function to generate cache key from args

    Returns:
        Decorator function

    Example:
        @cached(ttl_seconds=300, namespace="work_items")
        async def get_work_item(self, work_item_id: int):
            return await self._fetch_work_item(work_item_id)
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache = get_cache()

            # Generate cache key
            if key_func:
                cache_key_suffix = key_func(*args, **kwargs)
            else:
                # Skip 'self' argument if present
                cache_args = args[1:] if args and hasattr(args[0], '__dict__') else args
                cache_key_suffix = make_cache_key(*cache_args, **kwargs)

            cache_key = f"{namespace}:{func.__name__}:{cache_key_suffix}"

            # Try to get from cache
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                return cached_value

            # Call function and cache result
            result = await func(*args, **kwargs)
            cache.set(cache_key, result, ttl_seconds)

            return result

        return wrapper
    return decorator


def invalidate_cache(namespace: str = "", key: Optional[str] = None):
    """
    Invalidate cache entries.

    Args:
        namespace: Namespace to invalidate (all entries with this prefix)
        key: Specific key to invalidate
    """
    cache = get_cache()

    if key:
        cache.invalidate(key)
    elif namespace:
        cache.invalidate_prefix(f"{namespace}:")
    else:
        cache.clear()


class CachedService:
    """
    Base class for services with caching support.

    Provides helper methods for cache management.
    """

    def __init__(self, cache_namespace: str, cache_ttl: int = 300):
        """
        Initialize cached service.

        Args:
            cache_namespace: Namespace for this service's cache entries
            cache_ttl: Default TTL for cache entries
        """
        self.cache_namespace = cache_namespace
        self.cache_ttl = cache_ttl
        self.cache = get_cache()

    def _make_cache_key(self, *parts) -> str:
        """Create cache key with namespace."""
        key_parts = [self.cache_namespace] + [str(p) for p in parts]
        return ':'.join(key_parts)

    def _get_cached(self, *key_parts) -> Optional[Any]:
        """Get value from cache."""
        key = self._make_cache_key(*key_parts)
        return self.cache.get(key)

    def _set_cached(self, value: Any, *key_parts, ttl: Optional[int] = None):
        """Set value in cache."""
        key = self._make_cache_key(*key_parts)
        self.cache.set(key, value, ttl or self.cache_ttl)

    def _invalidate_cached(self, *key_parts):
        """Invalidate specific cache entry."""
        key = self._make_cache_key(*key_parts)
        self.cache.invalidate(key)

    def _invalidate_all(self):
        """Invalidate all cache entries for this service."""
        self.cache.invalidate_prefix(f"{self.cache_namespace}:")

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return self.cache.get_stats()
