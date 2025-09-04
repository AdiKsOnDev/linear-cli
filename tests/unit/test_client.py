"""
Unit tests for Linear GraphQL client.
"""

import time
from unittest.mock import AsyncMock, Mock, patch

import pytest

from linear_cli.api.client import LinearClient, RateLimiter, ResponseCache
from linear_cli.config.manager import LinearConfig


class TestRateLimiter:
    """Unit tests for rate limiter."""

    @pytest.mark.asyncio
    async def test_acquire_within_limits(self):
        """Test rate limiter allows requests within limits."""
        limiter = RateLimiter(max_requests=2, time_window=1.0)

        # First request should go through immediately
        start_time = time.time()
        await limiter.acquire()
        elapsed = time.time() - start_time

        assert elapsed < 0.1  # Should be immediate
        assert len(limiter.requests) == 1

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_acquire_rate_limited(self):
        """Test rate limiter blocks when limits exceeded."""
        limiter = RateLimiter(max_requests=1, time_window=0.2)  # Shorter time window

        # First request
        await limiter.acquire()
        assert len(limiter.requests) == 1

        # Second request should be delayed
        start_time = time.time()
        await limiter.acquire()
        elapsed = time.time() - start_time

        # Should have waited at least 0.2 seconds
        assert elapsed >= 0.2
        assert len(limiter.requests) == 1  # Old request should be removed

    def test_cleanup_old_requests(self):
        """Test cleanup of old requests from tracking."""
        limiter = RateLimiter(max_requests=10, time_window=1.0)

        # Add some old requests
        now = time.time()
        limiter.requests = [now - 2.0, now - 1.5, now - 0.5]  # Mix of old and recent

        # Trigger cleanup by checking limits
        limiter.requests = [
            req_time
            for req_time in limiter.requests
            if now - req_time < limiter.time_window
        ]

        # Only the recent request should remain
        assert len(limiter.requests) == 1
        assert limiter.requests[0] == now - 0.5


class TestResponseCache:
    """Unit tests for response cache."""

    def test_cache_init(self):
        """Test cache initialization."""
        cache = ResponseCache(ttl=60, max_size=100)
        assert cache.ttl == 60
        assert cache.max_size == 100
        assert len(cache.cache) == 0

    def test_cache_get_set(self):
        """Test basic cache operations."""
        cache = ResponseCache(ttl=300)

        # Cache miss
        result = cache.get("test_query", {"var": "value"})
        assert result is None

        # Cache set and hit
        test_data = {"data": {"viewer": {"name": "Test"}}}
        cache.set("test_query", {"var": "value"}, test_data)

        result = cache.get("test_query", {"var": "value"})
        assert result == test_data

    def test_cache_expiration(self):
        """Test cache entry expiration."""
        cache = ResponseCache(ttl=0.1)  # Very short TTL

        # Set and immediately get
        cache.set("test_query", {}, {"data": "test"})
        assert cache.get("test_query", {}) is not None

        # Wait for expiration
        time.sleep(0.2)
        assert cache.get("test_query", {}) is None

    def test_cache_max_size_eviction(self):
        """Test cache eviction when max size reached."""
        cache = ResponseCache(ttl=300, max_size=2)

        # Fill cache to max size
        cache.set("query1", {}, {"data": "1"})
        cache.set("query2", {}, {"data": "2"})
        assert len(cache.cache) == 2

        # Add one more - should evict oldest
        cache.set("query3", {}, {"data": "3"})
        assert len(cache.cache) == 2
        assert cache.get("query1", {}) is None  # Should be evicted
        assert cache.get("query2", {}) is not None
        assert cache.get("query3", {}) is not None


class TestLinearClient:
    """Unit tests for LinearClient."""

    def test_client_init(self):
        """Test client initialization."""
        config = LinearConfig()

        with patch("src.linear-cli.api.auth.LinearAuthenticator") as mock_auth:
            client = LinearClient(config=config, authenticator=mock_auth)

            assert client.config == config
            assert client.authenticator == mock_auth
            assert isinstance(client.rate_limiter, RateLimiter)
            assert isinstance(client.cache, ResponseCache)

    @pytest.mark.asyncio
    async def test_get_viewer_success(self):
        """Test successful get_viewer call."""
        config = LinearConfig()
        mock_auth = Mock()
        mock_auth.get_access_token.return_value = "test_token"

        with patch(
            "src.linear-cli.api.client.LinearClient.execute_query"
        ) as mock_execute:
            mock_execute.return_value = {"viewer": {"name": "Test User"}}

            client = LinearClient(config=config, authenticator=mock_auth)
            result = await client.get_viewer()

            assert result == {"name": "Test User"}
            mock_execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_teams_success(self):
        """Test successful get_teams call."""
        config = LinearConfig()
        mock_auth = Mock()
        mock_auth.get_access_token.return_value = "test_token"

        with patch(
            "src.linear-cli.api.client.LinearClient.execute_query"
        ) as mock_execute:
            mock_execute.return_value = {
                "teams": {
                    "nodes": [
                        {"id": "1", "name": "Team 1", "key": "T1"},
                        {"id": "2", "name": "Team 2", "key": "T2"},
                    ]
                }
            }

            client = LinearClient(config=config, authenticator=mock_auth)
            result = await client.get_teams()

            assert len(result) == 2
            assert result[0]["name"] == "Team 1"
            assert result[1]["name"] == "Team 2"
            mock_execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_query_with_cache_hit(self):
        """Test query execution with cache hit."""
        config = LinearConfig()
        mock_auth = Mock()
        mock_auth.get_access_token.return_value = "test_token"

        client = LinearClient(config=config, authenticator=mock_auth)

        # Pre-populate cache
        cached_response = {"data": {"cached": True}}
        client.cache.set("test query", {}, cached_response)

        with patch("httpx.AsyncClient") as mock_http:
            result = await client.execute_query("test query", {})

            assert result == cached_response
            mock_http.assert_not_called()  # Should not make HTTP request

    @pytest.mark.asyncio
    async def test_execute_query_http_success(self):
        """Test successful HTTP query execution."""
        config = LinearConfig()
        mock_auth = Mock()
        mock_auth.get_access_token.return_value = "test_token"

        # Mock the GQL client in the client module
        with patch("src.linear-cli.api.client.client.Client") as mock_gql_client_class:
            mock_gql_client = mock_gql_client_class.return_value
            mock_gql_client.execute_async = AsyncMock(return_value={"test": "success"})

            client = LinearClient(config=config, authenticator=mock_auth)
            result = await client.execute_query("{ viewer { id } }", {})

            assert result == {"test": "success"}
            mock_gql_client.execute_async.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_query_unauthenticated(self):
        """Test query execution when not authenticated."""
        config = LinearConfig()
        mock_auth = Mock()
        mock_auth.get_access_token.return_value = None

        client = LinearClient(config=config, authenticator=mock_auth)

        with pytest.raises(Exception, match="No valid access token available"):
            await client.execute_query("{ viewer { id } }", {})

    @pytest.mark.asyncio
    async def test_test_connection_success(self):
        """Test successful connection test."""
        config = LinearConfig()
        mock_auth = Mock()

        with patch("src.linear-cli.api.client.LinearClient.get_viewer") as mock_viewer:
            mock_viewer.return_value = {
                "name": "Test User",
                "organization": {"name": "Test Org"},
            }

            client = LinearClient(config=config, authenticator=mock_auth)
            start_time = time.time()
            result = await client.test_connection()

            assert result["success"] is True
            assert result["user"] == "Test User"
            assert result["organization"] == "Test Org"
            assert result["response_time"] >= 0
            assert result["response_time"] <= time.time() - start_time + 1

    @pytest.mark.asyncio
    async def test_test_connection_failure(self):
        """Test connection test failure."""
        config = LinearConfig()
        mock_auth = Mock()

        with patch("src.linear-cli.api.client.LinearClient.get_viewer") as mock_viewer:
            mock_viewer.side_effect = Exception("Connection failed")

            client = LinearClient(config=config, authenticator=mock_auth)
            result = await client.test_connection()

            assert result["success"] is False
            assert "Connection failed" in result["error"]
            assert "user" not in result
            assert "organization" not in result

    def test_generate_cache_key(self):
        """Test cache key generation."""
        config = LinearConfig()
        mock_auth = Mock()

        client = LinearClient(config=config, authenticator=mock_auth)

        # Test with different queries and variables
        key1 = client.cache._generate_key("query1", {"var": "value1"})
        key2 = client.cache._generate_key("query1", {"var": "value2"})
        key3 = client.cache._generate_key("query2", {"var": "value1"})

        assert key1 != key2  # Different variables
        assert key1 != key3  # Different queries
        assert key2 != key3  # Both different

    def test_client_configuration_applied(self):
        """Test that client configuration is properly applied."""
        config = LinearConfig(
            api_url="https://custom.api.url/graphql", timeout=60, cache_ttl=600
        )
        mock_auth = Mock()

        with patch("src.linear-cli.api.auth.LinearAuthenticator"):
            client = LinearClient(config=config, authenticator=mock_auth)

            assert client.config.api_url == "https://custom.api.url/graphql"
            assert client.config.timeout == 60
            assert client.cache.ttl == 600
