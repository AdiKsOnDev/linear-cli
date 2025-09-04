"""
Utility classes for Linear API client.

Provides rate limiting and response caching functionality.
"""

import asyncio
import json
import logging
import time
from typing import Any

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Simple rate limiter for API requests.

    Implements a token bucket algorithm to respect API rate limits.
    """

    def __init__(self, max_requests: int = 1000, time_window: int = 3600):
        """
        Initialize rate limiter.

        Args:
            max_requests: Maximum requests allowed in time window
            time_window: Time window in seconds (default 1 hour)
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests: list[float] = []
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        """
        Acquire permission to make a request.

        Blocks if rate limit would be exceeded.
        """
        async with self._lock:
            now = time.time()

            # Remove old requests outside the time window
            self.requests = [
                req_time
                for req_time in self.requests
                if now - req_time < self.time_window
            ]

            # Check if we can make another request
            if len(self.requests) >= self.max_requests:
                # Calculate how long to wait
                oldest_request = min(self.requests)
                wait_time = self.time_window - (now - oldest_request) + 1

                logger.warning(f"Rate limit reached, waiting {wait_time:.1f}s")
                await asyncio.sleep(wait_time)

                # Try again after waiting
                await self.acquire()
                return

            # Record this request
            self.requests.append(now)


class ResponseCache:
    """
    Simple in-memory cache for GraphQL responses.

    Caches responses based on query and variables hash.
    """

    def __init__(self, ttl: int = 300, max_size: int = 1000):
        """
        Initialize response cache.

        Args:
            ttl: Time to live in seconds
            max_size: Maximum number of cached responses
        """
        self.ttl = ttl
        self.max_size = max_size
        self.cache: dict[str, dict[str, Any]] = {}
        self._access_times: dict[str, float] = {}

    def _generate_key(self, query: str, variables: dict[str, Any] | None = None) -> str:
        """Generate cache key from query and variables."""
        key_data = {"query": query, "variables": variables or {}}
        return str(hash(json.dumps(key_data, sort_keys=True)))

    def get(
        self, query: str, variables: dict[str, Any] | None = None
    ) -> dict[str, Any] | None:
        """
        Get cached response.

        Args:
            query: GraphQL query string
            variables: Query variables

        Returns:
            Cached response or None if not found/expired
        """
        key = self._generate_key(query, variables)

        if key not in self.cache:
            return None

        cached_item = self.cache[key]
        cached_at = cached_item.get("cached_at", 0)

        # Check if expired
        if time.time() - cached_at > self.ttl:
            del self.cache[key]
            if key in self._access_times:
                del self._access_times[key]
            return None

        # Update access time
        self._access_times[key] = time.time()
        return cached_item.get("data")

    def set(
        self, query: str, variables: dict[str, Any] | None, data: dict[str, Any]
    ) -> None:
        """
        Cache response.

        Args:
            query: GraphQL query string
            variables: Query variables
            data: Response data to cache
        """
        key = self._generate_key(query, variables)

        # Evict oldest items if cache is full
        if len(self.cache) >= self.max_size:
            self._evict_oldest()

        self.cache[key] = {
            "data": data,
            "cached_at": time.time(),
        }
        self._access_times[key] = time.time()

    def _evict_oldest(self) -> None:
        """Evict the least recently used cache entry."""
        if not self._access_times:
            return

        oldest_key = min(self._access_times.keys(), key=lambda k: self._access_times[k])

        del self.cache[oldest_key]
        del self._access_times[oldest_key]

    def clear(self) -> None:
        """Clear all cached responses."""
        self.cache.clear()
        self._access_times.clear()
