"""Tests for performance optimization utilities."""

import asyncio
import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from linear_cli.utils.performance import (
    BatchProcessor,
    PersistentCache,
    ProgressTracker,
    cache_result,
    memoize_with_ttl,
    run_with_concurrency_limit,
)


class TestPersistentCache:
    """Test persistent cache functionality."""

    @pytest.fixture
    def temp_cache_dir(self):
        """Create temporary cache directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    @pytest.fixture
    def cache(self, temp_cache_dir):
        """Create cache instance with temp directory."""
        return PersistentCache(cache_dir=temp_cache_dir, default_ttl=60)

    def test_cache_set_and_get(self, cache):
        """Test basic cache set and get operations."""
        cache.set("test_key", "test_value")
        assert cache.get("test_key") == "test_value"

    def test_cache_get_nonexistent(self, cache):
        """Test getting nonexistent key returns None."""
        assert cache.get("nonexistent") is None

    def test_cache_expiry(self, cache):
        """Test cache expiry functionality."""
        # Set with very short TTL
        cache.set("expire_key", "expire_value", ttl=0.1)

        # Should be available immediately
        assert cache.get("expire_key") == "expire_value"

        # Wait for expiry
        time.sleep(0.2)

        # Should be expired
        assert cache.get("expire_key") is None

    def test_cache_delete(self, cache):
        """Test cache deletion."""
        cache.set("delete_key", "delete_value")
        assert cache.get("delete_key") == "delete_value"

        cache.delete("delete_key")
        assert cache.get("delete_key") is None

    def test_cache_clear(self, cache):
        """Test clearing all cache entries."""
        cache.set("key1", "value1")
        cache.set("key2", "value2")

        count = cache.clear()
        assert count == 2
        assert cache.get("key1") is None
        assert cache.get("key2") is None

    def test_cache_cleanup_expired(self, cache):
        """Test cleanup of expired entries."""
        # Set some entries with different TTLs
        cache.set("keep", "keep_value", ttl=60)
        cache.set("expire", "expire_value", ttl=0.1)

        time.sleep(0.2)

        count = cache.cleanup_expired()
        assert count == 1
        assert cache.get("keep") == "keep_value"
        assert cache.get("expire") is None


class TestCacheResultDecorator:
    """Test cache_result decorator."""

    @pytest.fixture
    def temp_cache_dir(self):
        """Create temporary cache directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    def test_cache_result_decorator(self, temp_cache_dir):
        """Test cache_result decorator functionality."""
        cache_instance = PersistentCache(cache_dir=temp_cache_dir, default_ttl=60)
        call_count = 0

        @cache_result(ttl=60, cache_instance=cache_instance)
        def expensive_function(x, y=10):
            nonlocal call_count
            call_count += 1
            return x + y

        # First call
        result1 = expensive_function(5, y=15)
        assert result1 == 20
        assert call_count == 1

        # Second call should use cache
        result2 = expensive_function(5, y=15)
        assert result2 == 20
        assert call_count == 1  # Should not increment

        # Different args should not use cache
        result3 = expensive_function(3, y=7)
        assert result3 == 10
        assert call_count == 2

    def test_cache_result_with_custom_key_func(self, temp_cache_dir):
        """Test cache_result with custom key function."""
        cache_instance = PersistentCache(cache_dir=temp_cache_dir, default_ttl=60)
        call_count = 0

        def key_func(x, y=10):
            return f"custom:{x}:{y}"

        @cache_result(ttl=60, cache_instance=cache_instance, key_func=key_func)
        def test_function(x, y=10):
            nonlocal call_count
            call_count += 1
            return x * y

        result1 = test_function(3, y=4)
        assert result1 == 12
        assert call_count == 1

        result2 = test_function(3, y=4)
        assert result2 == 12
        assert call_count == 1  # Cached


class TestMemoizeWithTTL:
    """Test memoize_with_ttl decorator."""

    def test_memoize_basic_functionality(self):
        """Test basic memoization functionality."""
        call_count = 0

        @memoize_with_ttl(ttl=60)
        def test_function(x, y=10):
            nonlocal call_count
            call_count += 1
            return x + y

        # First call
        result1 = test_function(5, y=15)
        assert result1 == 20
        assert call_count == 1

        # Second call should use cache
        result2 = test_function(5, y=15)
        assert result2 == 20
        assert call_count == 1

    def test_memoize_cache_expiry(self):
        """Test memoization cache expiry."""
        call_count = 0

        @memoize_with_ttl(ttl=0.1)  # Very short TTL
        def test_function(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        # First call
        result1 = test_function(5)
        assert result1 == 10
        assert call_count == 1

        # Second call immediately should use cache
        result2 = test_function(5)
        assert result2 == 10
        assert call_count == 1

        # Wait for expiry
        time.sleep(0.2)

        # Third call should execute again
        result3 = test_function(5)
        assert result3 == 10
        assert call_count == 2

    def test_memoize_cache_methods(self):
        """Test memoize cache management methods."""

        @memoize_with_ttl(ttl=60)
        def test_function(x):
            return x * 2

        test_function(5)
        test_function(10)

        # Check cache info
        info = test_function.cache_info()
        assert info["size"] == 2
        assert info["ttl"] == 60
        assert len(info["keys"]) == 2

        # Clear cache
        test_function.cache_clear()
        info = test_function.cache_info()
        assert info["size"] == 0


class TestBatchProcessor:
    """Test batch processing functionality."""

    @pytest.mark.asyncio
    async def test_batch_processor_size_trigger(self):
        """Test batch processing triggered by size."""
        processed_batches = []

        async def processor(items):
            processed_batches.append(items.copy())

        batch_processor = BatchProcessor(
            batch_size=3, timeout=10.0, processor=processor
        )

        # Add items one by one
        await batch_processor.add("item1")
        await batch_processor.add("item2")
        assert len(processed_batches) == 0  # No batch processed yet

        await batch_processor.add("item3")
        assert len(processed_batches) == 1  # Batch should be processed
        assert processed_batches[0] == ["item1", "item2", "item3"]

    @pytest.mark.asyncio
    async def test_batch_processor_timeout_trigger(self):
        """Test batch processing triggered by timeout."""
        processed_batches = []

        async def processor(items):
            processed_batches.append(items.copy())

        batch_processor = BatchProcessor(
            batch_size=10, timeout=0.1, processor=processor
        )

        await batch_processor.add("item1")
        assert len(processed_batches) == 0

        # Wait for timeout
        await asyncio.sleep(0.2)
        await batch_processor.add("item2")

        # Should have processed the first item due to timeout
        assert len(processed_batches) == 1
        assert "item1" in processed_batches[0]

    @pytest.mark.asyncio
    async def test_batch_processor_flush(self):
        """Test manual batch flush."""
        processed_batches = []

        async def processor(items):
            processed_batches.append(items.copy())

        batch_processor = BatchProcessor(
            batch_size=10, timeout=10.0, processor=processor
        )

        await batch_processor.add("item1")
        await batch_processor.add("item2")
        assert len(processed_batches) == 0

        await batch_processor.flush()
        assert len(processed_batches) == 1
        assert processed_batches[0] == ["item1", "item2"]

    @pytest.mark.asyncio
    async def test_batch_processor_context_manager(self):
        """Test batch processor as context manager."""
        processed_batches = []

        async def processor(items):
            processed_batches.append(items.copy())

        async with BatchProcessor(
            batch_size=10, timeout=10.0, processor=processor
        ) as batch_processor:
            await batch_processor.add("item1")
            await batch_processor.add("item2")
            assert len(processed_batches) == 0

        # Should flush on exit
        assert len(processed_batches) == 1
        assert processed_batches[0] == ["item1", "item2"]


class TestProgressTracker:
    """Test progress tracking functionality."""


    def test_progress_tracker_eta_calculation(self):
        """Test ETA calculation."""
        tracker = ProgressTracker(total=10, description="Test", show_progress=False)

        # No progress yet
        assert tracker.eta is None

        # Add some progress
        tracker.update(2)
        time.sleep(0.1)  # Small delay to get elapsed time

        eta = tracker.eta
        assert eta is not None
        assert eta > 0



class TestRunWithConcurrencyLimit:
    """Test concurrent task execution."""

    @pytest.mark.asyncio
    async def test_run_with_concurrency_limit(self):
        """Test running tasks with concurrency limit."""
        call_order = []

        async def task(i):
            call_order.append(i)
            await asyncio.sleep(0.01)  # Small delay
            return i * 2

        tasks = [lambda i=i: task(i) for i in range(5)]

        with patch("linear_cli.utils.performance.ProgressTracker"):
            task_results = await run_with_concurrency_limit(
                tasks, max_concurrent=2, show_progress=False
            )

        # Check results
        assert len(task_results) == 5
        for i, result in enumerate(task_results):
            assert result == i * 2

    @pytest.mark.asyncio
    async def test_run_with_concurrency_limit_error_handling(self):
        """Test error handling in concurrent execution."""

        async def good_task():
            return "success"

        async def bad_task():
            raise ValueError("Task failed")

        tasks = [good_task, bad_task, good_task]

        with patch("linear_cli.utils.performance.ProgressTracker"):
            results = await run_with_concurrency_limit(
                tasks, max_concurrent=2, show_progress=False
            )

        assert len(results) == 3
        assert results[0] == "success"
        assert isinstance(results[1], ValueError)
        assert results[2] == "success"

    @pytest.mark.asyncio
    async def test_run_with_progress_display(self):
        """Test concurrent execution with progress display."""

        async def task():
            await asyncio.sleep(0.01)
            return "done"

        tasks = [task for _ in range(3)]

        with patch("linear_cli.utils.performance.ProgressTracker") as mock_tracker:
            mock_instance = Mock()
            mock_tracker.return_value.__enter__.return_value = mock_instance

            results = await run_with_concurrency_limit(
                tasks, max_concurrent=2, show_progress=True
            )

        # Should have created progress tracker
        mock_tracker.assert_called_once_with(3, "Executing tasks", True)

        # Should have updated progress for each task
        assert mock_instance.update.call_count == 3

        # All tasks should succeed
        assert all(result == "done" for result in results)
