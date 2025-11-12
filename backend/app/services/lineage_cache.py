"""
Lineage caching layer with TTL-based expiration for Unity Catalog lineage queries.

This module provides an in-memory cache to reduce expensive lineage queries
to Unity Catalog and improve API response times.
"""

from datetime import datetime, timedelta
from threading import Lock
from typing import Any, Dict, Optional
from dataclasses import dataclass, field

import structlog

from app.core.config import settings

logger = structlog.get_logger(__name__)


@dataclass
class CacheEntry:
    """Represents a single cache entry with TTL metadata."""

    value: Any
    timestamp: datetime
    ttl_seconds: int

    def is_expired(self) -> bool:
        """
        Check if the cache entry has exceeded its TTL.

        Returns:
            True if the entry is expired, False otherwise
        """
        expiration_time = self.timestamp + timedelta(seconds=self.ttl_seconds)
        return datetime.now() >= expiration_time


@dataclass
class CacheStatistics:
    """Cache performance statistics."""

    hits: int = 0
    misses: int = 0
    evictions: int = 0
    total_queries: int = 0

    @property
    def hit_rate(self) -> float:
        """
        Calculate cache hit rate.

        Returns:
            Hit rate as a percentage (0.0 to 100.0)
        """
        if self.total_queries == 0:
            return 0.0
        return (self.hits / self.total_queries) * 100.0


class LineageCache:
    """
    Thread-safe in-memory cache for lineage queries with TTL-based expiration.

    This cache stores lineage query results to reduce repeated expensive
    queries to Unity Catalog. Entries expire after a configurable TTL period.

    Attributes:
        default_ttl_seconds: Default time-to-live for cache entries in seconds
        max_size: Maximum number of entries before eviction
        _cache: Internal storage for cache entries
        _lock: Thread lock for safe concurrent access
        _stats: Cache performance statistics
    """

    def __init__(
        self,
        default_ttl_seconds: int = 900,
        max_size: int = 1000,
    ) -> None:
        """
        Initialize the lineage cache.

        Args:
            default_ttl_seconds: Default TTL in seconds (default: 900 = 15 minutes)
            max_size: Maximum number of cache entries (default: 1000)
        """
        self.default_ttl_seconds = default_ttl_seconds
        self.max_size = max_size
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = Lock()
        self._stats = CacheStatistics()

        logger.info(
            "lineage_cache_initialized",
            default_ttl_seconds=default_ttl_seconds,
            max_size=max_size,
        )

    def make_key(
        self,
        table_name: str,
        direction: str,
        depth: int,
        **kwargs,
    ) -> str:
        """
        Generate a deterministic cache key from lineage parameters.

        Args:
            table_name: Full table name (catalog.schema.table)
            direction: Lineage direction ("upstream", "downstream", or "both")
            depth: Traversal depth
            **kwargs: Additional optional parameters (e.g., include_columns)

        Returns:
            Unique cache key string in format: lineage:{table}:{direction}:{depth}[:extras]

        Example:
            >>> cache = LineageCache()
            >>> cache.make_key("catalog.schema.table", "both", 3)
            'lineage:catalog.schema.table:both:3'
            >>> cache.make_key("catalog.schema.table", "both", 3, include_columns=True)
            'lineage:catalog.schema.table:both:3:include_columns=True'
        """
        normalized_table = table_name.lower().strip()
        normalized_direction = direction.lower().strip()
        base_key = f"lineage:{normalized_table}:{normalized_direction}:{depth}"

        # Add optional parameters in sorted order for deterministic keys
        if kwargs:
            extras = ":".join(f"{k}={v}" for k, v in sorted(kwargs.items()))
            return f"{base_key}:{extras}"

        return base_key

    def get(self, cache_key: str) -> Optional[Any]:
        """
        Retrieve a value from the cache.

        Args:
            cache_key: The cache key to look up

        Returns:
            Cached value if found and not expired, None otherwise
        """
        with self._lock:
            self._stats.total_queries += 1

            entry = self._cache.get(cache_key)

            if entry is None:
                self._stats.misses += 1
                logger.debug("cache_miss", cache_key=cache_key)
                return None

            if entry.is_expired():
                self._evict_entry(cache_key)
                self._stats.misses += 1
                logger.debug(
                    "cache_miss_expired",
                    cache_key=cache_key,
                    age_seconds=(datetime.now() - entry.timestamp).total_seconds(),
                )
                return None

            self._stats.hits += 1
            logger.debug("cache_hit", cache_key=cache_key)
            return entry.value

    def set(
        self,
        cache_key: str,
        value: Any,
        ttl_seconds: Optional[int] = None,
    ) -> None:
        """
        Store a value in the cache with TTL.

        Args:
            cache_key: The cache key
            value: The value to cache
            ttl_seconds: Optional TTL override (uses default if not provided)
        """
        with self._lock:
            # Enforce max size by evicting oldest entry
            if len(self._cache) >= self.max_size and cache_key not in self._cache:
                self._evict_oldest()

            ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl_seconds

            entry = CacheEntry(
                value=value,
                timestamp=datetime.now(),
                ttl_seconds=ttl,
            )

            self._cache[cache_key] = entry

            logger.debug(
                "cache_set",
                cache_key=cache_key,
                ttl_seconds=ttl,
                cache_size=len(self._cache),
            )

    def clear(self) -> None:
        """Clear all entries from the cache."""
        with self._lock:
            cleared_count = len(self._cache)
            self._cache.clear()
            logger.info("cache_cleared", cleared_entries=cleared_count)

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache performance statistics.

        Returns:
            Dictionary containing cache metrics
        """
        with self._lock:
            return {
                "hits": self._stats.hits,
                "misses": self._stats.misses,
                "evictions": self._stats.evictions,
                "total_queries": self._stats.total_queries,
                "hit_rate": self._stats.hit_rate,
                "current_size": len(self._cache),
                "max_size": self.max_size,
                "default_ttl_seconds": self.default_ttl_seconds,
            }

    def _evict_entry(self, cache_key: str) -> None:
        """
        Evict a specific cache entry.

        Args:
            cache_key: The key to evict
        """
        if cache_key in self._cache:
            del self._cache[cache_key]
            self._stats.evictions += 1
            logger.debug("cache_evicted", cache_key=cache_key)

    def _evict_oldest(self) -> None:
        """Evict the oldest cache entry to make room for new entries."""
        if not self._cache:
            return

        oldest_key = min(
            self._cache.keys(),
            key=lambda k: self._cache[k].timestamp,
        )

        self._evict_entry(oldest_key)
        logger.debug("cache_evicted_oldest", cache_key=oldest_key)


# Global cache instance
_global_cache: Optional[LineageCache] = None
_global_cache_lock = Lock()


def get_lineage_cache() -> LineageCache:
    """
    Get the global lineage cache instance (singleton pattern).

    Returns:
        The global LineageCache instance
    """
    global _global_cache

    if _global_cache is None:
        with _global_cache_lock:
            if _global_cache is None:
                # Use settings from config - convert minutes to seconds
                ttl_minutes = getattr(settings, "LINEAGE_CACHE_TTL_MINUTES", 15)
                ttl_seconds = ttl_minutes * 60
                max_size = getattr(settings, "LINEAGE_CACHE_MAX_SIZE", 1000)

                _global_cache = LineageCache(
                    default_ttl_seconds=ttl_seconds,
                    max_size=max_size,
                )

                logger.info(
                    "global_lineage_cache_initialized",
                    ttl_minutes=ttl_minutes,
                    ttl_seconds=ttl_seconds,
                    max_size=max_size,
                )

    return _global_cache
