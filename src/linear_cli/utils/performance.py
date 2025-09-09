"""
Performance optimization utilities for Linearator.

Provides caching, batching, and async utilities for improved performance.
"""

import asyncio
import functools
import hashlib
import json
import logging
import time
from collections.abc import Callable
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


class PersistentCache:
    """
    Persistent disk-based cache with TTL support.

    Stores cache data in user's cache directory with automatic cleanup.
    """

    def __init__(self, cache_dir: Path | None = None, default_ttl: int = 300):
        """
        Initialize persistent cache.

        Args:
            cache_dir: Directory to store cache files (default: ~/.cache/linear-cli)
            default_ttl: Default TTL in seconds
        """
        if cache_dir is None:
            cache_dir = Path.home() / ".cache" / "linear-cli"

        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.default_ttl = default_ttl

    def _get_cache_file(self, key: str) -> Path:
        """Get cache file path for a key."""
        # Hash the key to create a safe filename
        key_hash = hashlib.sha256(key.encode()).hexdigest()[:16]
        return self.cache_dir / f"{key_hash}.cache"

    def _is_expired(self, cache_data: dict[str, Any]) -> bool:
        """Check if cached data is expired."""
        if "expires_at" not in cache_data:
            return True

        expires_at = datetime.fromisoformat(cache_data["expires_at"])
        return datetime.now() > expires_at

    def get(self, key: str) -> Any | None:
        """Get value from cache."""
        cache_file = self._get_cache_file(key)

        if not cache_file.exists():
            return None

        try:
            with open(cache_file, encoding="utf-8") as f:
                cache_data = json.load(f)

            if self._is_expired(cache_data):
                cache_file.unlink(missing_ok=True)
                return None

            logger.debug(f"Cache hit for key: {key}")
            return cache_data["value"]

        except (json.JSONDecodeError, OSError, KeyError) as e:
            logger.warning(f"Error reading cache file {cache_file}: {e}")
            cache_file.unlink(missing_ok=True)
            return None

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Set value in cache with TTL."""
        if ttl is None:
            ttl = self.default_ttl

        expires_at = datetime.now() + timedelta(seconds=ttl)
        cache_data = {
            "value": value,
            "expires_at": expires_at.isoformat(),
            "created_at": datetime.now().isoformat(),
        }

        cache_file = self._get_cache_file(key)

        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
            logger.debug(f"Cached value for key: {key} (TTL: {ttl}s)")
        except (json.JSONEncodeError, OSError) as e:
            logger.warning(f"Error writing cache file {cache_file}: {e}")

    def delete(self, key: str) -> None:
        """Delete key from cache."""
        cache_file = self._get_cache_file(key)
        cache_file.unlink(missing_ok=True)

    def clear(self) -> int:
        """Clear all cache files. Returns number of files deleted."""
        count = 0
        for cache_file in self.cache_dir.glob("*.cache"):
            try:
                cache_file.unlink()
                count += 1
            except OSError:
                pass

        logger.info(f"Cleared {count} cache files")
        return count

    def cleanup_expired(self) -> int:
        """Remove expired cache files. Returns number of files deleted."""
        count = 0
        for cache_file in self.cache_dir.glob("*.cache"):
            try:
                with open(cache_file, encoding="utf-8") as f:
                    cache_data = json.load(f)

                if self._is_expired(cache_data):
                    cache_file.unlink()
                    count += 1

            except (json.JSONDecodeError, OSError, KeyError):
                # If we can't read it, delete it
                cache_file.unlink(missing_ok=True)
                count += 1

        if count > 0:
            logger.info(f"Cleaned up {count} expired cache files")
        return count


def cache_result(
    ttl: int = 300,
    cache_instance: PersistentCache | None = None,
    key_func: Callable[..., str] | None = None,
) -> Callable[..., Callable[..., T]]:
    """
    Decorator to cache function results.

    Args:
        ttl: Time to live in seconds
        cache_instance: Cache instance to use (default: global cache)
        key_func: Function to generate cache key (default: str(args) + str(kwargs))
    """
    if cache_instance is None:
        cache_instance = PersistentCache()

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # Default key generation
                key_parts = [func.__name__, str(args), str(sorted(kwargs.items()))]
                cache_key = hashlib.sha256("|".join(key_parts).encode()).hexdigest()

            # Try to get from cache
            result = cache_instance.get(cache_key)
            if result is not None:
                return result  # type: ignore[no-any-return]

            # Execute function and cache result
            result = func(*args, **kwargs)
            cache_instance.set(cache_key, result, ttl)

            return result

        return wrapper

    return decorator


class BatchProcessor:
    """
    Utility for batching operations to improve performance.

    Collects items and processes them in batches either when:
    - Batch size is reached
    - Timeout occurs
    - Manual flush is called
    """

    def __init__(
        self,
        batch_size: int = 50,
        timeout: float = 1.0,
        processor: Callable[[list[Any]], Any] | None = None,
    ):
        """
        Initialize batch processor.

        Args:
            batch_size: Maximum items per batch
            timeout: Maximum time to wait before processing batch
            processor: Function to process batches
        """
        self.batch_size = batch_size
        self.timeout = timeout
        self.processor = processor

        self._items: list[Any] = []
        self._last_batch_time = time.time()
        self._lock = asyncio.Lock()

    async def add(self, item: Any) -> None:
        """Add item to batch."""
        async with self._lock:
            self._items.append(item)

            # Check if we should process the batch
            should_process = (
                len(self._items) >= self.batch_size
                or time.time() - self._last_batch_time >= self.timeout
            )

            if should_process:
                await self._process_batch()

    async def flush(self) -> None:
        """Process any remaining items in the batch."""
        async with self._lock:
            if self._items:
                await self._process_batch()

    async def _process_batch(self) -> None:
        """Process current batch of items."""
        if not self._items:
            return

        items_to_process = self._items.copy()
        self._items.clear()
        self._last_batch_time = time.time()

        logger.debug(f"Processing batch of {len(items_to_process)} items")

        if self.processor:
            try:
                await self.processor(items_to_process)
            except Exception as e:
                logger.error(f"Error processing batch: {e}")

    async def __aenter__(self) -> "BatchProcessor":
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        await self.flush()


class ProgressTracker:
    """
    Track and display progress for long-running operations.

    Provides both programmatic progress tracking and optional
    console display with Rich progress bars.
    """

    def __init__(
        self, total: int, description: str = "Processing", show_progress: bool = True
    ):
        """
        Initialize progress tracker.

        Args:
            total: Total number of items to process
            description: Description for progress display
            show_progress: Whether to show progress bar
        """
        self.total = total
        self.description = description
        self.show_progress = show_progress

        self.current = 0
        self.start_time = time.time()

        self._progress = None
        self._task_id = None

        if show_progress:
            try:
                from rich.progress import (
                    BarColumn,
                    Progress,
                    TextColumn,
                    TimeRemainingColumn,
                )

                self._progress = Progress(
                    TextColumn("[progress.description]{task.description}"),
                    BarColumn(),
                    "[progress.percentage]{task.percentage:>3.0f}%",
                    TimeRemainingColumn(),
                )
                self._task_id = self._progress.add_task(description, total=total)
            except ImportError:
                logger.warning("Rich not available, progress display disabled")

    def update(self, amount: int = 1) -> None:
        """Update progress by specified amount."""
        self.current = min(self.current + amount, self.total)

        if self._progress and self._task_id is not None:
            self._progress.update(self._task_id, advance=amount)

    def set_description(self, description: str) -> None:
        """Update progress description."""
        self.description = description
        if self._progress and self._task_id is not None:
            self._progress.update(self._task_id, description=description)

    @property
    def percentage(self) -> float:
        """Get current progress percentage."""
        if self.total == 0:
            return 100.0
        return (self.current / self.total) * 100

    @property
    def elapsed_time(self) -> float:
        """Get elapsed time in seconds."""
        return time.time() - self.start_time

    @property
    def eta(self) -> float | None:
        """Get estimated time to completion in seconds."""
        if self.current == 0:
            return None

        elapsed = self.elapsed_time
        rate = self.current / elapsed
        remaining = self.total - self.current

        if rate > 0:
            return remaining / rate
        return None

    def __enter__(self) -> "ProgressTracker":
        if self._progress:
            self._progress.start()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if self._progress:
            self._progress.stop()


async def run_with_concurrency_limit(
    tasks: list[Callable[[], Any]],
    max_concurrent: int = 10,
    show_progress: bool = False,
) -> list[Any]:
    """
    Run tasks with concurrency limit.

    Args:
        tasks: List of async callables to execute
        max_concurrent: Maximum concurrent tasks
        show_progress: Whether to show progress bar

    Returns:
        List of results in same order as tasks
    """
    semaphore = asyncio.Semaphore(max_concurrent)
    results: list[Any] = [None] * len(tasks)

    async def run_task(i: int, task: Callable[[], Any]) -> None:
        async with semaphore:
            try:
                results[i] = await task()
            except Exception as e:
                logger.error(f"Task {i} failed: {e}")
                results[i] = e

    with ProgressTracker(len(tasks), "Executing tasks", show_progress) as progress:

        async def track_task(i: int, task: Callable[[], Any]) -> None:
            await run_task(i, task)
            progress.update()

        await asyncio.gather(*[track_task(i, task) for i, task in enumerate(tasks)])

    return results


def memoize_with_ttl(ttl: int = 300) -> Callable[..., Callable[..., Any]]:
    """
    Memoization decorator with TTL.

    Caches function results in memory with automatic expiration.
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        cache: dict[str, dict[str, Any]] = {}

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Generate cache key
            key = f"{func.__name__}:{hash(str(args) + str(sorted(kwargs.items())))}"

            # Check if cached result exists and is valid
            if key in cache:
                entry = cache[key]
                if time.time() - entry["timestamp"] < ttl:
                    logger.debug(f"Memory cache hit for {func.__name__}")
                    return entry["result"]
                else:
                    del cache[key]

            # Execute function and cache result
            result = func(*args, **kwargs)
            cache[key] = {"result": result, "timestamp": time.time()}

            return result

        wrapper.cache_clear = lambda: cache.clear()  # type: ignore[attr-defined]
        wrapper.cache_info = lambda: {  # type: ignore[attr-defined]
            "size": len(cache),
            "ttl": ttl,
            "keys": list(cache.keys()),
        }

        return wrapper

    return decorator
