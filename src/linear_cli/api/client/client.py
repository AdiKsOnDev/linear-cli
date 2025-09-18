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

    async def _handle_transport_error(
        self, error: TransportError, attempt: int
    ) -> tuple[bool, int]:
        """
        Handle transport errors with appropriate retry logic.

        Args:
            error: Transport error to handle
            attempt: Current attempt number

        Returns:
            Tuple of (should_retry, wait_time)

        Raises:
            AuthenticationError: If authentication fails
            RateLimitError: If rate limit exceeded
            LinearAPIError: For non-retryable errors
        """
        if not (hasattr(error, "response") and error.response):
            raise LinearAPIError(f"Transport error: {error}") from error

        status_code = error.response.status_code

        if status_code == 401:
            # Token expired, try to refresh
            try:
                self.authenticator.refresh_token()
                # Reset client to use new token
                self._gql_client = None
                self._transport = None
                return True, 0  # Continue immediately
            except AuthenticationError as auth_err:
                raise AuthenticationError(
                    "Authentication failed - please login again"
                ) from auth_err

        elif status_code == 429:
            # Rate limited
            wait_time = 60  # Default wait time
            if "Retry-After" in error.response.headers:
                wait_time = int(error.response.headers["Retry-After"])

            if attempt < self.config.max_retries:
                logger.warning(
                    f"Rate limited, waiting {wait_time}s (attempt {attempt + 1})"
                )
                return True, wait_time
            else:
                raise RateLimitError("Rate limit exceeded") from None

        elif 500 <= status_code < 600:
            # Server error, retry
            if attempt < self.config.max_retries:
                wait_time = 2**attempt  # Exponential backoff
                logger.warning(f"Server error {status_code}, retrying in {wait_time}s")
                return True, wait_time

        # Non-retryable error
        raise LinearAPIError(f"Transport error: {error}") from error

    async def _handle_timeout_error(
        self, error: Exception, attempt: int
    ) -> tuple[bool, int]:
        """
        Handle timeout errors with retry logic.

        Args:
            error: Exception to handle
            attempt: Current attempt number

        Returns:
            Tuple of (should_retry, wait_time)

        Raises:
            LinearAPIError: If non-retryable or max retries exceeded
        """
        if attempt < self.config.max_retries and "timeout" in str(error).lower():
            wait_time = 2**attempt
            logger.warning(f"Timeout error, retrying in {wait_time}s")
            return True, wait_time

        # Non-retryable or max retries exceeded
        raise LinearAPIError(f"Query execution failed: {error}") from error

    async def _execute_query_with_retries(
        self, query: str, variables: dict[str, Any] | None, use_cache: bool
    ) -> dict[str, Any]:
        """
        Execute GraphQL query with retry logic.

        Args:
            query: GraphQL query string
            variables: Query variables
            use_cache: Whether to cache results

        Returns:
            Query result data
        """
        client = self._get_gql_client()

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
                should_retry, wait_time = await self._handle_transport_error(e, attempt)
                if should_retry:
                    if wait_time > 0:
                        await asyncio.sleep(wait_time)
                    continue

            except Exception as e:
                should_retry, wait_time = await self._handle_timeout_error(e, attempt)
                if should_retry:
                    await asyncio.sleep(wait_time)
                    continue

        # Should not reach here
        raise LinearAPIError("Max retries exceeded")

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
            return await self._execute_query_with_retries(query, variables, use_cache)
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

        CRITICAL FIX DOCUMENTATION:
        This query includes the 'states' field which was missing in previous versions,
        causing complete failure of all state update operations. Here's what happened:

        PROBLEM:
        - The GraphQL query was missing the 'states { nodes { ... } }' field
        - When issue commands tried to resolve state names to IDs, they got empty state lists
        - This caused ALL state update operations to fail silently or with confusing errors
        - Users couldn't set states on issue creation or updates using either text or numeric inputs

        ROOT CAUSE:
        - The Linear API requires explicit field selection in GraphQL queries
        - Team states are not returned by default - they must be explicitly requested
        - Without state data, the state resolution logic had no states to match against

        SOLUTION:
        - Added complete 'states' field with nested 'nodes' containing id, name, type, color
        - This provides all necessary state information for the numeric state enum system
        - Now state resolution works for both numeric (0-6) and text-based state inputs

        IMPACT:
        - Fixes the core state update functionality that was completely broken
        - Enables the numeric state enum feature (0=Canceled, 1=Backlog, etc.)
        - Restores backward compatibility with text-based state names
        - Essential for issue create and update commands to function properly

        Returns:
            List of team information including complete state data
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
                    states {
                        nodes {
                            id
                            name
                            type
                            color
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
        milestone_id: str | None = None,
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
            milestone_id: Milestone ID

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
        if milestone_id:
            input_data["projectMilestoneId"] = milestone_id

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
        project_id: str | None = None,
        milestone_id: str | None = None,
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
            project_id: Project ID
            milestone_id: Milestone ID

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
        if project_id is not None:
            input_data["projectId"] = project_id
        if milestone_id is not None:
            input_data["projectMilestoneId"] = milestone_id

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

    async def get_projects(self, limit: int = 50) -> dict[str, Any]:
        """
        Get list of projects.

        Args:
            limit: Maximum number of projects to return

        Returns:
            Dictionary containing projects data
        """
        from ..queries import GET_PROJECTS_QUERY

        variables = {"first": limit}
        result = await self.execute_query(GET_PROJECTS_QUERY, variables)
        projects_data = result.get("projects", {})
        return dict(projects_data) if isinstance(projects_data, dict) else {}

    async def get_project(self, project_id: str) -> dict[str, Any] | None:
        """
        Get a single project by ID or name.

        Args:
            project_id: Project ID or name

        Returns:
            Project data or None if not found
        """
        from ..queries import GET_PROJECT_QUERY

        # Try direct ID lookup first
        try:
            variables = {"id": project_id}
            result = await self.execute_query(GET_PROJECT_QUERY, variables)
            project_data = result.get("project")

            if project_data:
                return dict(project_data) if isinstance(project_data, dict) else None
        except Exception as e:
            # WHY: Direct ID lookup can fail for two reasons:
            # 1. Invalid UUID format (user provided a name, not ID)
            # 2. Entity not found (invalid ID)
            # We log for debugging but continue to name-based search as fallback
            import logging

            logging.debug(f"Direct project ID lookup failed: {e}")
            # Continue to name-based search

        # WHY: Use lightweight query first to find project by name, then detailed query for full data
        # This is more efficient than fetching full details for all projects just to find one
        from ..queries import FIND_PROJECT_BY_NAME_QUERY, GET_PROJECT_QUERY

        search_variables: dict[str, Any] = {"first": 100}
        result = await self.execute_query(FIND_PROJECT_BY_NAME_QUERY, search_variables)
        projects_data = result.get("projects", {})

        for project in projects_data.get("nodes", []):
            if project.get("name", "").lower() == project_id.lower():
                # Found project by name, now get full details using direct ID lookup
                variables = {"id": project["id"]}
                result = await self.execute_query(GET_PROJECT_QUERY, variables)
                project_data = result.get("project")
                if project_data:
                    return (
                        dict(project_data) if isinstance(project_data, dict) else None
                    )

        return None

    async def create_project_update(
        self,
        project_id: str,
        content: str,
        health: str | None = None,
    ) -> dict[str, Any]:
        """
        Create a project update.

        Args:
            project_id: Project ID or name
            content: Update content/message
            health: Project health status

        Returns:
            Created project update data
        """
        from ..queries import CREATE_PROJECT_UPDATE_MUTATION

        # First get the project to ensure we have the ID
        project = await self.get_project(project_id)
        if not project:
            raise ValueError(f"Project not found: {project_id}")

        input_data = {
            "projectId": project["id"],
            "body": content,
        }

        if health:
            input_data["health"] = health

        variables = {"input": input_data}
        result = await self.execute_query(CREATE_PROJECT_UPDATE_MUTATION, variables)

        project_update_data = result.get("projectUpdateCreate", {}).get("projectUpdate")
        return (
            dict(project_update_data) if isinstance(project_update_data, dict) else {}
        )

    async def get_project_updates(
        self, project_id: str, limit: int = 20
    ) -> dict[str, Any]:
        """
        Get project updates for a project.

        Args:
            project_id: Project ID or name
            limit: Maximum number of updates to return

        Returns:
            Dictionary containing project updates data
        """
        from ..queries import GET_PROJECT_UPDATES_QUERY

        # First get the project to ensure we have the ID
        project = await self.get_project(project_id)
        if not project:
            raise ValueError(f"Project not found: {project_id}")

        variables = {"projectId": project["id"], "first": limit}
        result = await self.execute_query(GET_PROJECT_UPDATES_QUERY, variables)
        updates_data = result.get("projectUpdates", {})
        return dict(updates_data) if isinstance(updates_data, dict) else {}

    async def create_project(
        self,
        name: str,
        description: str | None = None,
        team_ids: list[str] | None = None,
        lead_id: str | None = None,
        state: str = "planned",
        start_date: str | None = None,
        target_date: str | None = None,
    ) -> dict[str, Any]:
        """
        Create a new project.

        Args:
            name: Project name
            description: Project description
            team_ids: List of team IDs to associate with the project
            lead_id: Project lead user ID
            state: Project state (planned, started, paused, completed, canceled)
            start_date: Start date (ISO 8601 format)
            target_date: Target completion date (ISO 8601 format)

        Returns:
            Created project data
        """
        from ..queries import CREATE_PROJECT_MUTATION

        input_data: dict[str, Any] = {"name": name}

        if description:
            input_data["description"] = description
        if team_ids:
            input_data["teamIds"] = team_ids
        if lead_id:
            input_data["leadId"] = lead_id
        if state:
            input_data["state"] = state
        if start_date:
            input_data["startDate"] = start_date
        if target_date:
            input_data["targetDate"] = target_date

        variables = {"input": input_data}
        result = await self.execute_query(CREATE_PROJECT_MUTATION, variables)
        project_create_data = result.get("projectCreate", {})
        return (
            dict(project_create_data) if isinstance(project_create_data, dict) else {}
        )

    # Milestone methods
    async def get_milestones(
        self,
        project_id: str | None = None,
        limit: int = 50,
        after: str | None = None,
        target_date_after: str | None = None,
        target_date_before: str | None = None,
    ) -> dict[str, Any]:
        """
        Get list of milestones with optional filtering.

        Retrieves milestones from Linear with support for project scoping,
        pagination, and date range filtering. Results are sorted by target date.

        Args:
            project_id: Filter by project ID - restricts to specific project
            limit: Maximum milestones to return (1-100, default: 50)
            after: Cursor for pagination - get milestones after this point
            target_date_after: ISO 8601 date - only milestones due after this
            target_date_before: ISO 8601 date - only milestones due before this

        Returns:
            Dict with 'nodes' (milestone list) and 'pageInfo' (pagination data)
            Each milestone includes project, creator, target date, and issue count

        Raises:
            LinearAPIError: If API request fails
            ValueError: If date filters are invalid ISO 8601 format

        Example:
            # Get upcoming milestones for a project
            milestones = await client.get_milestones(
                project_id="proj_123",
                target_date_after="2024-01-01T00:00:00Z",
                limit=20
            )
        """
        from ..queries import GET_MILESTONES_QUERY, build_milestone_filter

        # Build filter
        filter_kwargs: dict[str, Any] = {}
        if project_id:
            filter_kwargs["project_id"] = project_id
        if target_date_after:
            filter_kwargs["target_date_after"] = target_date_after
        if target_date_before:
            filter_kwargs["target_date_before"] = target_date_before

        milestone_filter = (
            build_milestone_filter(**filter_kwargs) if filter_kwargs else None
        )

        variables = {
            "first": limit,
            "after": after,
            "filter": milestone_filter,
        }

        result = await self.execute_query(GET_MILESTONES_QUERY, variables)
        milestones_data = result.get("projectMilestones", {})
        return dict(milestones_data) if isinstance(milestones_data, dict) else {}

    async def get_milestone(self, milestone_id: str) -> dict[str, Any] | None:
        """
        Get a single milestone by ID.

        Args:
            milestone_id: Milestone ID

        Returns:
            Milestone data or None if not found
        """
        from ..queries import GET_MILESTONE_QUERY

        variables = {"id": milestone_id}
        result = await self.execute_query(GET_MILESTONE_QUERY, variables)
        milestone_data = result.get("projectMilestone")
        return dict(milestone_data) if isinstance(milestone_data, dict) else None

    async def get_project_milestones(
        self, project_id: str, limit: int = 50, after: str | None = None
    ) -> dict[str, Any]:
        """
        Get milestones for a specific project.

        Args:
            project_id: Project ID
            limit: Maximum number of milestones to return
            after: Cursor for pagination

        Returns:
            Project milestones data with pagination info
        """
        from ..queries import GET_PROJECT_MILESTONES_QUERY

        variables = {
            "projectId": project_id,
            "first": limit,
            "after": after,
        }

        result = await self.execute_query(GET_PROJECT_MILESTONES_QUERY, variables)
        milestones_data = result.get("projectMilestones", {})
        return dict(milestones_data) if isinstance(milestones_data, dict) else {}

    async def create_milestone(
        self,
        name: str,
        project_id: str,
        description: str | None = None,
        target_date: str | None = None,
    ) -> dict[str, Any]:
        """
        Create a new milestone.

        Args:
            name: Milestone name
            project_id: Project ID to associate milestone with
            description: Milestone description
            target_date: Target completion date (ISO 8601 format)

        Returns:
            Created milestone data
        """
        from ..queries import CREATE_MILESTONE_MUTATION

        input_data: dict[str, Any] = {
            "name": name,
            "projectId": project_id,
        }

        if description:
            input_data["description"] = description
        if target_date:
            input_data["targetDate"] = target_date

        variables = {"input": input_data}
        result = await self.execute_query(CREATE_MILESTONE_MUTATION, variables)
        milestone_create_data = result.get("projectMilestoneCreate", {})
        return (
            dict(milestone_create_data)
            if isinstance(milestone_create_data, dict)
            else {}
        )

    async def update_milestone(
        self,
        milestone_id: str,
        name: str | None = None,
        description: str | None = None,
        target_date: str | None = None,
    ) -> dict[str, Any]:
        """
        Update an existing milestone.

        Args:
            milestone_id: Milestone ID
            name: New milestone name
            description: New milestone description
            target_date: New target completion date (ISO 8601 format)

        Returns:
            Updated milestone data
        """
        from ..queries import UPDATE_MILESTONE_MUTATION

        input_data: dict[str, Any] = {}

        if name is not None:
            input_data["name"] = name
        if description is not None:
            input_data["description"] = description
        if target_date is not None:
            input_data["targetDate"] = target_date

        variables = {"id": milestone_id, "input": input_data}
        result = await self.execute_query(UPDATE_MILESTONE_MUTATION, variables)
        milestone_update_data = result.get("projectMilestoneUpdate", {})
        return (
            dict(milestone_update_data)
            if isinstance(milestone_update_data, dict)
            else {}
        )

    async def delete_milestone(self, milestone_id: str) -> bool:
        """
        Delete a milestone.

        Args:
            milestone_id: Milestone ID

        Returns:
            True if successful
        """
        from ..queries import DELETE_MILESTONE_MUTATION

        variables = {"id": milestone_id}
        result = await self.execute_query(DELETE_MILESTONE_MUTATION, variables)
        delete_data = result.get("projectMilestoneDelete", {})
        success_value = (
            delete_data.get("success", False)
            if isinstance(delete_data, dict)
            else False
        )
        return bool(success_value)

    async def assign_issue_to_milestone(
        self, issue_id: str, milestone_id: str | None
    ) -> dict[str, Any]:
        """
        Assign an issue to a milestone or remove milestone assignment.

        Args:
            issue_id: Issue ID or identifier
            milestone_id: Milestone ID (None to remove assignment)

        Returns:
            Updated issue data
        """
        from ..queries import ASSIGN_ISSUE_TO_MILESTONE_MUTATION

        # If using identifier, get the actual ID first
        if "-" in issue_id and not issue_id.startswith("issue_"):
            issue = await self.get_issue(issue_id)
            if not issue:
                raise LinearAPIError(f"Issue not found: {issue_id}")
            issue_id = issue["id"]

        variables = {"issueId": issue_id, "milestoneId": milestone_id}
        result = await self.execute_query(ASSIGN_ISSUE_TO_MILESTONE_MUTATION, variables)
        issue_update_data = result.get("issueUpdate", {})
        return dict(issue_update_data) if isinstance(issue_update_data, dict) else {}

    async def resolve_milestone_id(
        self, milestone_identifier: str, project_id: str | None = None
    ) -> str | None:
        """
        Resolve milestone name or ID to actual milestone ID.
        WHY: Users prefer friendly milestone names ("Sprint 1") but Linear API
        requires milestone IDs. This provides name-to-ID resolution with optional
        project scoping to handle duplicate milestone names across projects.
        SEARCH STRATEGY:
        - First checks if input looks like milestone ID (starts with "milestone_" or >30 chars)
        - For names, searches project-scoped milestones first (more efficient)
        - Falls back to organization-wide search if no project specified
        - Case-insensitive matching for user convenience
        Args:
            milestone_identifier: Milestone name ("Sprint 1") or ID ("milestone_123")
            project_id: Optional project ID for scoped search - improves performance
                       and handles duplicate names across projects
        Returns:
            Milestone ID string, or None if not found
            Example:
            # Resolve milestone name within project context
            milestone_id = await client.resolve_milestone_id("Sprint 1", "proj_123")
        """
        # If it looks like an ID, return as-is
        if (
            milestone_identifier.startswith("milestone_")
            or len(milestone_identifier) > 30
        ):
            return milestone_identifier

        # Search for milestone by name  
        # NOTE: Temporarily searching all milestones due to GraphQL filter issues
        # TODO: Fix project-scoped milestone filtering
        milestones_data = await self.get_milestones(limit=100)

        nodes = milestones_data.get("nodes", [])
        for milestone in nodes:
            if milestone.get("name", "").lower() == milestone_identifier.lower():
                return milestone.get("id")

        return None

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
