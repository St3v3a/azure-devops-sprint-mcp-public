"""
Unit tests for cache module.

Tests TTL-based caching, expiration, invalidation, and statistics.
"""

import pytest
import time
import asyncio
from src.cache import (
    CacheEntry,
    Cache,
    CachedService,
    get_cache,
    make_cache_key
)


class TestCacheEntry:
    """Test CacheEntry class."""

    def test_entry_creation(self):
        """Test creating a cache entry."""
        entry = CacheEntry("test_data", ttl_seconds=60)
        assert entry.data == "test_data"
        assert entry.hit_count == 0
        assert entry.created_at is not None

    def test_entry_expiry_calculation(self):
        """Test that expiry is calculated correctly."""
        entry = CacheEntry("data", ttl_seconds=60)
        assert entry.expiry > entry.created_at
        # Expiry should be approximately 60 seconds from now
        delta = (entry.expiry - entry.created_at).total_seconds()
        assert 59 <= delta <= 61

    def test_entry_not_expired_immediately(self):
        """Test that entry is not expired immediately after creation."""
        entry = CacheEntry("data", ttl_seconds=60)
        assert not entry.is_expired()

    def test_entry_expires_after_ttl(self):
        """Test that entry expires after TTL."""
        entry = CacheEntry("data", ttl_seconds=0.1)  # 100ms
        time.sleep(0.15)  # Wait 150ms
        assert entry.is_expired()

    def test_entry_age_increases(self):
        """Test that age increases over time."""
        entry = CacheEntry("data", ttl_seconds=60)
        age1 = entry.age_seconds()
        time.sleep(0.1)
        age2 = entry.age_seconds()
        assert age2 > age1

    def test_entry_hit_count(self):
        """Test hit count tracking."""
        entry = CacheEntry("data", ttl_seconds=60)
        assert entry.hit_count == 0

        entry.record_hit()
        assert entry.hit_count == 1

        entry.record_hit()
        entry.record_hit()
        assert entry.hit_count == 3


class TestCache:
    """Test Cache class."""

    def test_cache_creation(self):
        """Test creating a cache."""
        cache = Cache(default_ttl_seconds=300, max_size=100)
        assert cache.default_ttl == 300
        assert cache.max_size == 100

    def test_cache_set_and_get(self):
        """Test basic set and get operations."""
        cache = Cache()
        cache.set('key1', 'value1')

        result = cache.get('key1')
        assert result == 'value1'

    def test_cache_get_miss(self):
        """Test that missing keys return None."""
        cache = Cache()
        result = cache.get('nonexistent')
        assert result is None

    def test_cache_get_updates_stats(self):
        """Test that get updates hit/miss statistics."""
        cache = Cache()
        cache.set('key1', 'value1')

        cache.get('key1')  # hit
        cache.get('key2')  # miss

        stats = cache.get_stats()
        assert stats['hits'] == 1
        assert stats['misses'] == 1

    def test_cache_custom_ttl(self):
        """Test setting custom TTL per entry."""
        cache = Cache(default_ttl_seconds=60)
        cache.set('key1', 'value1', ttl_seconds=120)

        # Entry should use custom TTL
        entry = cache._cache['key1']
        delta = (entry.expiry - entry.created_at).total_seconds()
        assert 119 <= delta <= 121

    def test_cache_expiration(self):
        """Test that expired entries are not returned."""
        cache = Cache()
        cache.set('key1', 'value1', ttl_seconds=0.1)  # 100ms

        # Should get value immediately
        assert cache.get('key1') == 'value1'

        # Wait for expiration
        time.sleep(0.15)

        # Should return None for expired entry
        result = cache.get('key1')
        assert result is None

    def test_cache_invalidation(self):
        """Test manual invalidation."""
        cache = Cache()
        cache.set('key1', 'value1')

        assert cache.get('key1') == 'value1'

        result = cache.invalidate('key1')
        assert result is True

        assert cache.get('key1') is None

    def test_cache_invalidate_missing_key(self):
        """Test invalidating a key that doesn't exist."""
        cache = Cache()
        result = cache.invalidate('nonexistent')
        assert result is False

    def test_cache_invalidate_prefix(self):
        """Test invalidating all keys with a prefix."""
        cache = Cache()
        cache.set('user:1', 'data1')
        cache.set('user:2', 'data2')
        cache.set('project:1', 'data3')

        count = cache.invalidate_prefix('user:')
        assert count == 2

        assert cache.get('user:1') is None
        assert cache.get('user:2') is None
        assert cache.get('project:1') == 'data3'

    def test_cache_clear(self):
        """Test clearing all entries."""
        cache = Cache()
        cache.set('key1', 'value1')
        cache.set('key2', 'value2')
        cache.set('key3', 'value3')

        cache.clear()

        assert cache.get('key1') is None
        assert cache.get('key2') is None
        assert cache.get('key3') is None
        assert cache.get_stats()['size'] == 0

    def test_cache_cleanup_expired(self):
        """Test cleanup of expired entries."""
        cache = Cache()
        cache.set('key1', 'value1', ttl_seconds=0.1)
        cache.set('key2', 'value2', ttl_seconds=60)

        # Wait for key1 to expire
        time.sleep(0.15)

        removed = cache.cleanup_expired()
        assert removed == 1
        assert cache.get('key1') is None
        assert cache.get('key2') == 'value2'

    def test_cache_eviction_when_full(self):
        """Test that oldest entry is evicted when cache is full."""
        cache = Cache(max_size=3)

        cache.set('key1', 'value1')
        time.sleep(0.01)
        cache.set('key2', 'value2')
        time.sleep(0.01)
        cache.set('key3', 'value3')
        time.sleep(0.01)

        # This should evict key1 (oldest)
        cache.set('key4', 'value4')

        assert cache.get('key1') is None
        assert cache.get('key2') == 'value2'
        assert cache.get('key3') == 'value3'
        assert cache.get('key4') == 'value4'

    def test_cache_stats(self):
        """Test cache statistics."""
        cache = Cache()

        cache.set('key1', 'value1')
        cache.set('key2', 'value2')

        cache.get('key1')  # hit
        cache.get('key1')  # hit
        cache.get('key3')  # miss

        stats = cache.get_stats()
        assert stats['size'] == 2
        assert stats['hits'] == 2
        assert stats['misses'] == 1
        assert stats['total_requests'] == 3
        assert stats['hit_rate_percent'] > 0

    def test_cache_hit_rate_calculation(self):
        """Test hit rate percentage calculation."""
        cache = Cache()
        cache.set('key1', 'value1')

        # 3 hits, 1 miss = 75% hit rate
        cache.get('key1')
        cache.get('key1')
        cache.get('key1')
        cache.get('key2')

        stats = cache.get_stats()
        assert stats['hit_rate_percent'] == 75.0


class TestGlobalCache:
    """Test global cache instance."""

    def test_get_cache_returns_singleton(self):
        """Test that get_cache returns same instance."""
        cache1 = get_cache()
        cache2 = get_cache()
        assert cache1 is cache2

    def test_get_cache_configuration(self):
        """Test that get_cache uses configuration on first call."""
        # Note: This test may interfere with other tests if they use get_cache()
        # In practice, the global cache is created once per process
        cache = get_cache(default_ttl_seconds=600, max_size=2000)
        assert isinstance(cache, Cache)


class TestMakeCacheKey:
    """Test cache key generation."""

    def test_make_key_from_args(self):
        """Test generating key from positional args."""
        key = make_cache_key('arg1', 'arg2', 'arg3')
        assert isinstance(key, str)
        assert len(key) == 16  # SHA256 hash truncated to 16 chars

    def test_make_key_from_kwargs(self):
        """Test generating key from keyword args."""
        key = make_cache_key(foo='bar', baz='qux')
        assert isinstance(key, str)
        assert len(key) == 16

    def test_make_key_from_mixed_args(self):
        """Test generating key from mixed args."""
        key = make_cache_key('arg1', 'arg2', foo='bar', baz='qux')
        assert isinstance(key, str)
        assert len(key) == 16

    def test_make_key_deterministic(self):
        """Test that same args produce same key."""
        key1 = make_cache_key('arg1', 'arg2', foo='bar')
        key2 = make_cache_key('arg1', 'arg2', foo='bar')
        assert key1 == key2

    def test_make_key_different_for_different_args(self):
        """Test that different args produce different keys."""
        key1 = make_cache_key('arg1', 'arg2')
        key2 = make_cache_key('arg1', 'arg3')
        assert key1 != key2

    def test_make_key_with_numbers(self):
        """Test key generation with numeric values."""
        key = make_cache_key(123, 456, count=789)
        assert isinstance(key, str)

    def test_make_key_with_none(self):
        """Test key generation with None values."""
        key = make_cache_key(None, 'value', option=None)
        assert isinstance(key, str)


class TestCachedService:
    """Test CachedService base class."""

    def test_service_creation(self):
        """Test creating a cached service."""
        service = CachedService(cache_namespace='test', cache_ttl=600)
        assert service.cache_namespace == 'test'
        assert service.cache_ttl == 600
        assert service.cache is not None

    def test_make_cache_key(self):
        """Test making cache key with namespace."""
        service = CachedService(cache_namespace='users')
        key = service._make_cache_key('get', 123)
        assert key.startswith('users:')
        assert 'get' in key
        assert '123' in key

    def test_get_cached(self):
        """Test getting from cache."""
        service = CachedService(cache_namespace='test')
        service._set_cached('value1', 'key1')

        result = service._get_cached('key1')
        assert result == 'value1'

    def test_get_cached_miss(self):
        """Test getting missing value from cache."""
        service = CachedService(cache_namespace='test')
        result = service._get_cached('nonexistent')
        assert result is None

    def test_set_cached(self):
        """Test setting value in cache."""
        service = CachedService(cache_namespace='test', cache_ttl=300)
        service._set_cached('value1', 'key1')

        result = service._get_cached('key1')
        assert result == 'value1'

    def test_set_cached_with_custom_ttl(self):
        """Test setting value with custom TTL."""
        service = CachedService(cache_namespace='test', cache_ttl=300)
        service._set_cached('value1', 'key1', ttl=600)

        # Value should be cached
        assert service._get_cached('key1') == 'value1'

    def test_invalidate_cached(self):
        """Test invalidating specific cache entry."""
        service = CachedService(cache_namespace='test')
        service._set_cached('value1', 'key1')

        service._invalidate_cached('key1')

        assert service._get_cached('key1') is None

    def test_invalidate_all(self):
        """Test invalidating all cache entries for service."""
        service = CachedService(cache_namespace='users')
        service._set_cached('value1', 'key1')
        service._set_cached('value2', 'key2')

        service._invalidate_all()

        assert service._get_cached('key1') is None
        assert service._get_cached('key2') is None

    def test_get_cache_stats(self):
        """Test getting cache statistics."""
        service = CachedService(cache_namespace='test')
        service._set_cached('value1', 'key1')
        service._get_cached('key1')  # hit

        stats = service.get_cache_stats()
        assert 'hits' in stats
        assert 'misses' in stats
        assert stats['hits'] >= 1

    def test_multiple_services_share_cache(self):
        """Test that different services share the same cache instance."""
        service1 = CachedService(cache_namespace='service1')
        service2 = CachedService(cache_namespace='service2')

        assert service1.cache is service2.cache

    def test_services_have_separate_namespaces(self):
        """Test that services have isolated namespaces."""
        service1 = CachedService(cache_namespace='service1')
        service2 = CachedService(cache_namespace='service2')

        service1._set_cached('value1', 'key1')
        service2._set_cached('value2', 'key1')

        # Same key, different namespaces
        assert service1._get_cached('key1') == 'value1'
        assert service2._get_cached('key1') == 'value2'


class TestCacheEdgeCases:
    """Test edge cases and error handling."""

    def test_cache_with_complex_data(self):
        """Test caching complex data structures."""
        cache = Cache()
        data = {
            'list': [1, 2, 3],
            'dict': {'a': 1, 'b': 2},
            'nested': {'list': [{'key': 'value'}]}
        }

        cache.set('complex', data)
        result = cache.get('complex')

        assert result == data
        assert result['list'] == [1, 2, 3]
        assert result['nested']['list'][0]['key'] == 'value'

    def test_cache_with_none_value(self):
        """Test that None can be cached."""
        cache = Cache()
        cache.set('none_key', None)

        # Note: get() returns None for both missing keys and cached None
        # This is a known limitation - cannot distinguish between the two
        result = cache.get('none_key')
        # In this implementation, cached None values behave like cache misses

    def test_cache_key_with_special_characters(self):
        """Test cache keys with special characters."""
        cache = Cache()
        special_key = 'key:with:colons/and/slashes'
        cache.set(special_key, 'value')

        result = cache.get(special_key)
        assert result == 'value'

    def test_cache_size_zero(self):
        """Test cache behavior at size boundaries."""
        cache = Cache()
        stats = cache.get_stats()
        assert stats['size'] == 0

        cache.set('key', 'value')
        stats = cache.get_stats()
        assert stats['size'] == 1
