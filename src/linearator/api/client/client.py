"""
Main Linear GraphQL API client.

Provides the primary LinearClient class for interacting with Linear's GraphQL API.
"""

import asyncio
import logging
import time
from typing import Any

from gql import Client, gql
from gql.transport.aiohttp import AIOHTTPTransport
from gql.transport.exceptions import TransportError

from ...config.manager import LinearConfig
from ..auth import AuthenticationError, LinearAuthenticator
from .exceptions import LinearAPIError, RateLimitError
from .utils import RateLimiter, ResponseCache

logger = logging.getLogger(__name__)


class LinearClient:
    """
    High-level client for Linear GraphQL API.

    Provides methods for common Linear operations with built-in
    authentication, rate limiting, and error handling.
    """

    def __init__(
        self,
        config: LinearConfig,
        authenticator: LinearAuthenticator | None = None,
        enable_cache: bool = True,
    ):
        """
        Initialize Linear client.

        Args:
            config: Linear configuration
            authenticator: Authentication handler
            enable_cache: Whether to enable response caching
        """
        self.config = config
        self.authenticator = authenticator or LinearAuthenticator(
            client_id=config.client_id,
            client_secret=config.client_secret,
            redirect_uri=config.redirect_uri,
        )

        # Initialize components
        self.rate_limiter = RateLimiter()
        self.cache = ResponseCache(ttl=config.cache_ttl) if enable_cache else None

        # GraphQL client will be initialized on first use
        self._gql_client: Client | None = None
        self._transport: AIOHTTPTransport | None = None

    def _get_auth_headers(self) -> dict[str, str]:
        """
        Get authentication headers for GraphQL requests.

        Constructs the required HTTP headers for Linear API authentication,
        including the Bearer token and content type. The authenticator handles
        token refresh automatically if needed.

        Returns:
            Dict containing Authorization and Content-Type headers

        Raises:
            AuthenticationError: If no valid access token is available
        """
        token = self.authenticator.get_access_token()
        if not token:
            raise AuthenticationError("No valid access token available")

        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    def _get_gql_client(self) -> Client:
        """
        Get or create GraphQL client with configured transport.

        Lazily initializes the GraphQL client with AIOHTTP transport configured
        for Linear's API endpoint. The client is reused for all subsequent requests
        to maintain connection pooling and performance.

        Returns:
            Configured GraphQL client instance
        """
        if self._gql_client is None:
            headers = self._get_auth_headers()

            self._transport = AIOHTTPTransport(
                url=self.config.api_url,
                headers=headers,
                timeout=self.config.timeout,  # AIOHTTPTransport expects int, not httpx.Timeout
            )

            self._gql_client = Client(
                transport=self._transport,
                fetch_schema_from_transport=False,  # Skip schema fetching for performance
            )

        return self._gql_client

    async def execute_query(
        self,
        query: str,
        variables: dict[str, Any] | None = None,
        use_cache: bool = True,
    ) -> dict[str, Any]:
        """
        Execute a GraphQL query.

        Args:
            query: GraphQL query string
            variables: Query variables
            use_cache: Whether to use cached results

        Returns:
            Query result data

        Raises:
            LinearAPIError: If query execution fails
            AuthenticationError: If authentication fails
        """
        # Check cache first
        if use_cache and self.cache:
            cached_result = self.cache.get(query, variables)
            if cached_result is not None:
                logger.debug("Returning cached result")
                return cached_result

        # Acquire rate limit token
        await self.rate_limiter.acquire()

        try:
            # Get GraphQL client
            client = self._get_gql_client()

            # Execute query with retry logic
            for attempt in range(self.config.max_retries + 1):
                try:
                    # Parse and execute query
                    parsed_query = gql(query)
                    result = await client.execute_async(
                        parsed_query, variable_values=variables
                    )

                    # Cache successful results
                    if use_cache and self.cache and result:
                        self.cache.set(query, variables, result)

                    return result

                except TransportError as e:
                    # Handle HTTP errors
                    if hasattr(e, "response") and e.response:
                        status_code = e.response.status_code

                        if status_code == 401:
                            # Token expired, try to refresh
                            try:
                                self.authenticator.refresh_token()
                                # Reset client to use new token
                                self._gql_client = None
                                self._transport = None
                                continue
                            except AuthenticationError as auth_err:
                                raise AuthenticationError(
                                    "Authentication failed - please login again"
                                ) from auth_err

                        elif status_code == 429:
                            # Rate limited
                            wait_time = 60  # Default wait time
                            if (
                                hasattr(e, "response")
                                and "Retry-After" in e.response.headers
                            ):
                                wait_time = int(e.response.headers["Retry-After"])

                            if attempt < self.config.max_retries:
                                logger.warning(
                                    f"Rate limited, waiting {wait_time}s (attempt {attempt + 1})"
                                )
                                await asyncio.sleep(wait_time)
                                continue
                            else:
                                raise RateLimitError("Rate limit exceeded") from None

                        elif 500 <= status_code < 600:
                            # Server error, retry
                            if attempt < self.config.max_retries:
                                wait_time = 2**attempt  # Exponential backoff
                                logger.warning(
                                    f"Server error {status_code}, retrying in {wait_time}s"
                                )
                                await asyncio.sleep(wait_time)
                                continue

                    # Non-retryable error or max retries reached
                    raise LinearAPIError(f"Transport error: {e}") from e

                except Exception as e:
                    if (
                        attempt < self.config.max_retries
                        and "timeout" in str(e).lower()
                    ):
                        # Timeout error, retry
                        wait_time = 2**attempt
                        logger.warning(f"Timeout error, retrying in {wait_time}s")
                        await asyncio.sleep(wait_time)
                        continue

                    # Other errors
                    raise LinearAPIError(f"Query execution failed: {e}") from e

            # Should not reach here
            raise LinearAPIError("Max retries exceeded")

        except AuthenticationError:
            # Re-raise authentication errors
            raise
        except (RateLimitError, LinearAPIError):
            # Re-raise API errors
            raise
        except Exception as e:
            # Catch-all for unexpected errors
            logger.error(f"Unexpected error in execute_query: {e}")
            raise LinearAPIError(f"Unexpected error: {e}") from e

    async def get_viewer(self) -> dict[str, Any]:
        """
        Get information about the authenticated user.

        Returns:
            User information
        """
        query = """
        query {
            viewer {
                id
                name
                email
                displayName
                avatarUrl
                isMe
                organization {
                    id
                    name
                    urlKey
                }
            }
        }
        """

        result = await self.execute_query(query)
        return result.get("viewer", {})

    async def get_teams(self) -> list[dict[str, Any]]:
        """
        Get list of teams accessible to the user.

        Returns:
            List of team information
        """
        query = """
        query {
            teams {
                nodes {
                    id
                    name
                    key
                    description
                    private
                    issueCount
                    memberCount
                }
            }
        }
        """

        result = await self.execute_query(query)
        return result.get("teams", {}).get("nodes", [])

    async def test_connection(self) -> dict[str, Any]:
        """
        Test API connection and authentication.

        Returns:
            Connection test results
        """
        start_time = time.time()

        try:
            viewer = await self.get_viewer()
            response_time = time.time() - start_time

            return {
                "success": True,
                "response_time": response_time,
                "user": viewer.get("name", "Unknown"),
                "organization": viewer.get("organization", {}).get("name", "Unknown"),
                "message": "Connection successful",
            }

        except Exception as e:
            response_time = time.time() - start_time

            return {
                "success": False,
                "response_time": response_time,
                "error": str(e),
                "message": "Connection failed",
            }

    def close(self) -> None:
        """Close the client and cleanup resources."""
        if self._transport:
            # Transport cleanup is handled by aiohttp
            pass

        if self.cache:
            self.cache.clear()

        logger.debug("Linear client closed")

    async def __aenter__(self) -> "LinearClient":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        self.close()
