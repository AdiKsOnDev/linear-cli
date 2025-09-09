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
            "Authorization": token,
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
        viewer_data = result.get("viewer", {})
        return dict(viewer_data) if isinstance(viewer_data, dict) else {}

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
                    members {
                        nodes {
                            id
                        }
                    }
                }
            }
        }
        """

        result = await self.execute_query(query)
        teams_data = result.get("teams", {}).get("nodes", [])
        return list(teams_data) if isinstance(teams_data, list) else []

    async def get_issues(
        self,
        team_id: str | None = None,
        team_key: str | None = None,
        assignee_id: str | None = None,
        assignee_email: str | None = None,
        state_name: str | None = None,
        labels: list[str] | None = None,
        priority: int | None = None,
        limit: int = 50,
        after: str | None = None,
        order_by: str = "updatedAt",
    ) -> dict[str, Any]:
        """
        Get list of issues with optional filtering.

        Args:
            team_id: Filter by team ID
            team_key: Filter by team key
            assignee_id: Filter by assignee ID
            assignee_email: Filter by assignee email
            state_name: Filter by state name
            labels: Filter by label names
            priority: Filter by priority (0=None, 1=Low, 2=Normal, 3=High, 4=Urgent)
            limit: Maximum number of issues to return
            after: Cursor for pagination
            order_by: Order by field (default: updatedAt)

        Returns:
            Issues data with pagination info
        """
        from ..queries import GET_ISSUES_QUERY, build_issue_filter

        # Build filter
        filter_kwargs: dict[str, Any] = {}
        if team_id:
            filter_kwargs["team_id"] = team_id
        elif team_key:
            filter_kwargs["team_key"] = team_key

        if assignee_id:
            filter_kwargs["assignee_id"] = assignee_id
        elif assignee_email:
            filter_kwargs["assignee_email"] = assignee_email

        if state_name:
            filter_kwargs["state_name"] = state_name

        if labels:
            filter_kwargs["labels"] = labels

        if priority is not None:
            filter_kwargs["priority"] = priority

        issue_filter = build_issue_filter(**filter_kwargs) if filter_kwargs else None

        variables = {
            "first": limit,
            "after": after,
            "filter": issue_filter,
            "orderBy": order_by,
        }

        result = await self.execute_query(GET_ISSUES_QUERY, variables)
        issues_data = result.get("issues", {})
        return dict(issues_data) if isinstance(issues_data, dict) else {}

    async def get_issue(self, issue_id: str) -> dict[str, Any] | None:
        """
        Get a single issue by ID or identifier.

        Args:
            issue_id: Issue ID or identifier (e.g., 'ENG-123')

        Returns:
            Issue data or None if not found
        """
        from ..queries import GET_ISSUE_QUERY, SEARCH_ISSUES_QUERY

        # If it looks like an identifier (has a dash), search for it
        if "-" in issue_id and not issue_id.startswith("issue_"):
            # Use search to find by identifier - more efficient than listing all issues
            variables = {"term": issue_id, "first": 1}
            result = await self.execute_query(SEARCH_ISSUES_QUERY, variables)
            search_results = result.get("searchIssues", {}).get("nodes", [])
            
            # Look for exact identifier match
            for issue in search_results:
                if issue.get("identifier") == issue_id:
                    return dict(issue) if isinstance(issue, dict) else None
            return None
        else:
            # Direct ID lookup
            variables = {"id": issue_id}
            result = await self.execute_query(GET_ISSUE_QUERY, variables)
            issue_data = result.get("issue")
            return dict(issue_data) if isinstance(issue_data, dict) else None

    async def create_issue(
        self,
        title: str,
        description: str | None = None,
        team_id: str | None = None,
        assignee_id: str | None = None,
        state_id: str | None = None,
        priority: int | None = None,
        label_ids: list[str] | None = None,
        parent_id: str | None = None,
        project_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Create a new issue.

        Args:
            title: Issue title
            description: Issue description
            team_id: Team ID (required)
            assignee_id: Assignee user ID
            state_id: Workflow state ID
            priority: Priority level (0=None, 1=Low, 2=Normal, 3=High, 4=Urgent)
            label_ids: List of label IDs
            parent_id: Parent issue ID
            project_id: Project ID

        Returns:
            Created issue data
        """
        from ..queries import CREATE_ISSUE_MUTATION

        # Build input
        input_data: dict[str, Any] = {"title": title}

        if description:
            input_data["description"] = description
        if team_id:
            input_data["teamId"] = team_id
        if assignee_id:
            input_data["assigneeId"] = assignee_id
        if state_id:
            input_data["stateId"] = state_id
        if priority is not None:
            input_data["priority"] = priority
        if label_ids:
            input_data["labelIds"] = label_ids
        if parent_id:
            input_data["parentId"] = parent_id
        if project_id:
            input_data["projectId"] = project_id

        variables = {"input": input_data}
        result = await self.execute_query(CREATE_ISSUE_MUTATION, variables)
        issue_create_data = result.get("issueCreate", {})
        return dict(issue_create_data) if isinstance(issue_create_data, dict) else {}

    async def update_issue(
        self,
        issue_id: str,
        title: str | None = None,
        description: str | None = None,
        assignee_id: str | None = None,
        state_id: str | None = None,
        priority: int | None = None,
        label_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Update an existing issue.

        Args:
            issue_id: Issue ID or identifier
            title: New title
            description: New description
            assignee_id: New assignee user ID
            state_id: New workflow state ID
            priority: New priority level
            label_ids: New list of label IDs

        Returns:
            Updated issue data
        """
        from ..queries import UPDATE_ISSUE_MUTATION

        # If using identifier, get the actual ID first
        if "-" in issue_id and not issue_id.startswith("issue_"):
            issue = await self.get_issue(issue_id)
            if not issue:
                raise LinearAPIError(f"Issue not found: {issue_id}")
            issue_id = issue["id"]

        # Build input
        input_data: dict[str, Any] = {}

        if title is not None:
            input_data["title"] = title
        if description is not None:
            input_data["description"] = description
        if assignee_id is not None:
            input_data["assigneeId"] = assignee_id
        if state_id is not None:
            input_data["stateId"] = state_id
        if priority is not None:
            input_data["priority"] = priority
        if label_ids is not None:
            input_data["labelIds"] = label_ids

        variables = {"id": issue_id, "input": input_data}
        result = await self.execute_query(UPDATE_ISSUE_MUTATION, variables)
        issue_update_data = result.get("issueUpdate", {})
        return dict(issue_update_data) if isinstance(issue_update_data, dict) else {}

    async def delete_issue(self, issue_id: str) -> bool:
        """
        Delete (archive) an issue.

        Args:
            issue_id: Issue ID or identifier

        Returns:
            True if successful
        """
        from ..queries import DELETE_ISSUE_MUTATION

        # If using identifier, get the actual ID first
        if "-" in issue_id and not issue_id.startswith("issue_"):
            issue = await self.get_issue(issue_id)
            if not issue:
                raise LinearAPIError(f"Issue not found: {issue_id}")
            issue_id = issue["id"]

        variables = {"id": issue_id}
        result = await self.execute_query(DELETE_ISSUE_MUTATION, variables)
        archive_data = result.get("issueArchive", {})
        success_value = (
            archive_data.get("success", False)
            if isinstance(archive_data, dict)
            else False
        )
        return bool(success_value)

    async def get_labels(
        self,
        team_id: str | None = None,
        limit: int = 100,
        after: str | None = None,
    ) -> dict[str, Any]:
        """
        Get list of labels.

        Args:
            team_id: Filter by team ID
            limit: Maximum number of labels to return
            after: Cursor for pagination

        Returns:
            Labels data with pagination info
        """
        from ..queries import GET_LABELS_QUERY

        filter_obj = {}
        if team_id:
            filter_obj = {"team": {"id": {"eq": team_id}}}

        variables = {
            "first": limit,
            "after": after,
            "filter": filter_obj if filter_obj else None,
        }

        result = await self.execute_query(GET_LABELS_QUERY, variables)
        labels_data = result.get("issueLabels", {})
        return dict(labels_data) if isinstance(labels_data, dict) else {}

    async def create_label(
        self,
        name: str,
        color: str = "#808080",
        description: str | None = None,
        team_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Create a new label.

        Args:
            name: Label name
            color: Label color (hex code)
            description: Label description
            team_id: Team ID (optional, for team-specific labels)

        Returns:
            Created label data
        """
        from ..queries import CREATE_LABEL_MUTATION

        input_data = {"name": name, "color": color}

        if description:
            input_data["description"] = description
        if team_id:
            input_data["teamId"] = team_id

        variables = {"input": input_data}
        result = await self.execute_query(CREATE_LABEL_MUTATION, variables)
        label_create_data = result.get("issueLabelCreate", {})
        return dict(label_create_data) if isinstance(label_create_data, dict) else {}

    async def get_users(
        self,
        team_id: str | None = None,
        active_only: bool = True,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """
        Get list of users.

        Args:
            team_id: Filter by team membership
            active_only: Only return active users
            limit: Maximum number of users to return

        Returns:
            List of user data
        """
        from ..queries import GET_USERS_QUERY, build_user_filter

        filter_kwargs = {}
        if active_only:
            filter_kwargs["active"] = True

        user_filter = build_user_filter(**filter_kwargs) if filter_kwargs else None

        variables = {
            "first": limit,
            "filter": user_filter,
        }

        result = await self.execute_query(GET_USERS_QUERY, variables)
        users_data = result.get("users", {})
        if isinstance(users_data, dict):
            nodes_data = users_data.get("nodes", [])
            return list(nodes_data) if isinstance(nodes_data, list) else []
        return []

    async def search_issues(
        self,
        query: str,
        team_id: str | None = None,
        team_key: str | None = None,
        assignee_id: str | None = None,
        assignee_email: str | None = None,
        state_name: str | None = None,
        labels: list[str] | None = None,
        priority: int | None = None,
        limit: int = 50,
        after: str | None = None,
    ) -> dict[str, Any]:
        """
        Search issues using full-text search with optional filtering.

        Args:
            query: Search query string
            team_id: Filter by team ID
            team_key: Filter by team key
            assignee_id: Filter by assignee ID
            assignee_email: Filter by assignee email
            state_name: Filter by state name
            labels: Filter by label names
            priority: Filter by priority (0=None, 1=Low, 2=Normal, 3=High, 4=Urgent)
            limit: Maximum number of issues to return
            after: Cursor for pagination

        Returns:
            Search results with pagination info
        """
        from ..queries import SEARCH_ISSUES_QUERY, build_issue_filter

        # Build filter - reuse the same filter builder from get_issues
        filter_kwargs: dict[str, Any] = {}
        if team_id:
            filter_kwargs["team_id"] = team_id
        elif team_key:
            filter_kwargs["team_key"] = team_key

        if assignee_id:
            filter_kwargs["assignee_id"] = assignee_id
        elif assignee_email:
            filter_kwargs["assignee_email"] = assignee_email

        if state_name:
            filter_kwargs["state_name"] = state_name

        if labels:
            filter_kwargs["labels"] = labels

        if priority is not None:
            filter_kwargs["priority"] = priority

        issue_filter = build_issue_filter(**filter_kwargs) if filter_kwargs else None

        variables = {
            "term": query,
            "first": limit,
            "after": after,
            "filter": issue_filter,
        }

        result = await self.execute_query(SEARCH_ISSUES_QUERY, variables)
        search_data = result.get("searchIssues", {})
        return dict(search_data) if isinstance(search_data, dict) else {}

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
