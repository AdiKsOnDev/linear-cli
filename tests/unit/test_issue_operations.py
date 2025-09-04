"""
Unit tests for issue operations in LinearClient.

Tests the issue CRUD operations and related functionality.
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from src.linear-cli.api.client import LinearClient
from src.linear-cli.api.client.exceptions import LinearAPIError
from src.linear-cli.config.manager import LinearConfig


@pytest.fixture
def mock_config():
    """Create a mock configuration for testing."""
    config = Mock(spec=LinearConfig)
    config.api_url = "https://api.linear.app/graphql"
    config.timeout = 30
    config.max_retries = 3
    config.cache_ttl = 300
    config.default_team_id = "team_123"
    config.default_team_key = "ENG"
    return config


@pytest.fixture
def mock_authenticator():
    """Create a mock authenticator for testing."""
    auth = Mock()
    auth.get_access_token.return_value = "test_token"
    auth.is_authenticated = True
    return auth


@pytest.fixture
def client(mock_config, mock_authenticator):
    """Create a LinearClient instance for testing."""
    return LinearClient(
        config=mock_config,
        authenticator=mock_authenticator,
        enable_cache=False,  # Disable cache for testing
    )


class TestIssueOperations:
    """Test suite for issue CRUD operations."""

    @pytest.mark.asyncio
    async def test_get_issues_basic(self, client):
        """Test basic issue listing."""
        mock_response = {
            "issues": {
                "nodes": [
                    {
                        "id": "issue_123",
                        "identifier": "ENG-123",
                        "title": "Test Issue",
                        "description": "Test description",
                        "state": {"id": "state_1", "name": "To Do"},
                        "priority": 2,
                        "team": {"id": "team_123", "key": "ENG"},
                        "assignee": None,
                        "labels": {"nodes": []},
                        "createdAt": "2024-01-01T00:00:00Z",
                        "updatedAt": "2024-01-01T00:00:00Z",
                    }
                ],
                "pageInfo": {"hasNextPage": False, "endCursor": None},
            }
        }

        with patch.object(
            client, "execute_query", new_callable=AsyncMock
        ) as mock_execute:
            mock_execute.return_value = mock_response

            result = await client.get_issues(limit=50)

            assert result == mock_response["issues"]
            mock_execute.assert_called_once()

            # Check the query was called with correct parameters
            call_args = mock_execute.call_args
            variables = call_args[0][1]  # Second argument (variables)
            assert variables["first"] == 50

    @pytest.mark.asyncio
    async def test_get_issues_with_filters(self, client):
        """Test issue listing with various filters."""
        mock_response = {
            "issues": {
                "nodes": [],
                "pageInfo": {"hasNextPage": False, "endCursor": None},
            }
        }

        with patch.object(
            client, "execute_query", new_callable=AsyncMock
        ) as mock_execute:
            mock_execute.return_value = mock_response

            await client.get_issues(
                team_key="ENG",
                assignee_email="test@example.com",
                state_name="In Progress",
                labels=["bug", "urgent"],
                priority=3,
                limit=25,
            )

            mock_execute.assert_called_once()

            # Verify the filter was built correctly
            call_args = mock_execute.call_args
            variables = call_args[0][1]  # Second argument (variables)

            assert variables["first"] == 25
            assert variables["filter"] is not None
            # The exact filter structure depends on build_issue_filter implementation

    @pytest.mark.asyncio
    async def test_get_issue_by_id(self, client):
        """Test getting a single issue by ID."""
        mock_response = {
            "issue": {
                "id": "issue_123",
                "identifier": "ENG-123",
                "title": "Test Issue",
                "description": "Test description",
            }
        }

        with patch.object(
            client, "execute_query", new_callable=AsyncMock
        ) as mock_execute:
            mock_execute.return_value = mock_response

            result = await client.get_issue("issue_123")

            assert result == mock_response["issue"]
            mock_execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_issue_by_identifier(self, client):
        """Test getting a single issue by identifier (e.g., ENG-123)."""
        # Mock the get_issues call that searches for the identifier
        mock_issues_response = {
            "nodes": [
                {
                    "id": "issue_123",
                    "identifier": "ENG-123",
                    "title": "Test Issue",
                }
            ]
        }

        with patch.object(
            client, "get_issues", new_callable=AsyncMock
        ) as mock_get_issues:
            mock_get_issues.return_value = mock_issues_response

            result = await client.get_issue("ENG-123")

            assert result == mock_issues_response["nodes"][0]
            mock_get_issues.assert_called_once_with(limit=1)

    @pytest.mark.asyncio
    async def test_get_issue_not_found(self, client):
        """Test getting an issue that doesn't exist."""
        with patch.object(
            client, "execute_query", new_callable=AsyncMock
        ) as mock_execute:
            mock_execute.return_value = {"issue": None}

            result = await client.get_issue("nonexistent_issue")

            assert result is None

    @pytest.mark.asyncio
    async def test_create_issue_success(self, client):
        """Test successful issue creation."""
        mock_response = {
            "issueCreate": {
                "success": True,
                "issue": {
                    "id": "issue_new",
                    "identifier": "ENG-124",
                    "title": "New Issue",
                    "description": "New issue description",
                },
            }
        }

        with patch.object(
            client, "execute_query", new_callable=AsyncMock
        ) as mock_execute:
            mock_execute.return_value = mock_response

            result = await client.create_issue(
                title="New Issue",
                description="New issue description",
                team_id="team_123",
                priority=2,
            )

            assert result == mock_response["issueCreate"]
            mock_execute.assert_called_once()

            # Check the input data was structured correctly
            call_args = mock_execute.call_args
            variables = call_args[0][1]  # Second argument (variables)
            input_data = variables["input"]

            assert input_data["title"] == "New Issue"
            assert input_data["description"] == "New issue description"
            assert input_data["teamId"] == "team_123"
            assert input_data["priority"] == 2

    @pytest.mark.asyncio
    async def test_create_issue_minimal(self, client):
        """Test issue creation with minimal required fields."""
        mock_response = {
            "issueCreate": {
                "success": True,
                "issue": {
                    "id": "issue_minimal",
                    "identifier": "ENG-125",
                    "title": "Minimal Issue",
                },
            }
        }

        with patch.object(
            client, "execute_query", new_callable=AsyncMock
        ) as mock_execute:
            mock_execute.return_value = mock_response

            result = await client.create_issue(title="Minimal Issue")

            assert result == mock_response["issueCreate"]

            # Check only title was set
            call_args = mock_execute.call_args
            variables = call_args[0][1]  # Second argument (variables)
            input_data = variables["input"]

            assert input_data["title"] == "Minimal Issue"
            assert "description" not in input_data
            assert "teamId" not in input_data

    @pytest.mark.asyncio
    async def test_update_issue_success(self, client):
        """Test successful issue update."""
        mock_response = {
            "issueUpdate": {
                "success": True,
                "issue": {
                    "id": "issue_123",
                    "identifier": "ENG-123",
                    "title": "Updated Title",
                    "description": "Updated description",
                },
            }
        }

        with patch.object(
            client, "execute_query", new_callable=AsyncMock
        ) as mock_execute:
            mock_execute.return_value = mock_response

            result = await client.update_issue(
                issue_id="issue_123",
                title="Updated Title",
                description="Updated description",
                priority=3,
            )

            assert result == mock_response["issueUpdate"]
            mock_execute.assert_called_once()

            # Check the update input
            call_args = mock_execute.call_args
            variables = call_args[0][1]  # Second argument (variables)
            assert variables["id"] == "issue_123"

            input_data = variables["input"]
            assert input_data["title"] == "Updated Title"
            assert input_data["description"] == "Updated description"
            assert input_data["priority"] == 3

    @pytest.mark.asyncio
    async def test_update_issue_by_identifier(self, client):
        """Test updating an issue using its identifier."""
        # Mock the get_issue call to resolve identifier to ID
        mock_issue = {
            "id": "issue_123",
            "identifier": "ENG-123",
            "title": "Original Title",
        }

        mock_update_response = {
            "issueUpdate": {
                "success": True,
                "issue": {
                    "id": "issue_123",
                    "identifier": "ENG-123",
                    "title": "Updated Title",
                },
            }
        }

        with (
            patch.object(client, "get_issue", new_callable=AsyncMock) as mock_get,
            patch.object(
                client, "execute_query", new_callable=AsyncMock
            ) as mock_execute,
        ):
            mock_get.return_value = mock_issue
            mock_execute.return_value = mock_update_response

            result = await client.update_issue(
                issue_id="ENG-123", title="Updated Title"
            )

            assert result == mock_update_response["issueUpdate"]
            mock_get.assert_called_once_with("ENG-123")
            mock_execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_issue_not_found(self, client):
        """Test updating an issue that doesn't exist."""
        with patch.object(client, "get_issue", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = None

            with pytest.raises(LinearAPIError, match="Issue not found"):
                await client.update_issue(issue_id="ENG-999", title="Updated Title")

    @pytest.mark.asyncio
    async def test_delete_issue_success(self, client):
        """Test successful issue deletion (archiving)."""
        mock_response = {"issueArchive": {"success": True}}

        with patch.object(
            client, "execute_query", new_callable=AsyncMock
        ) as mock_execute:
            mock_execute.return_value = mock_response

            result = await client.delete_issue("issue_123")

            assert result is True
            mock_execute.assert_called_once()

            # Check the correct ID was passed
            call_args = mock_execute.call_args
            variables = call_args[0][1]  # Second argument (variables)
            assert variables["id"] == "issue_123"

    @pytest.mark.asyncio
    async def test_delete_issue_by_identifier(self, client):
        """Test deleting an issue using its identifier."""
        mock_issue = {"id": "issue_123", "identifier": "ENG-123"}

        mock_delete_response = {"issueArchive": {"success": True}}

        with (
            patch.object(client, "get_issue", new_callable=AsyncMock) as mock_get,
            patch.object(
                client, "execute_query", new_callable=AsyncMock
            ) as mock_execute,
        ):
            mock_get.return_value = mock_issue
            mock_execute.return_value = mock_delete_response

            result = await client.delete_issue("ENG-123")

            assert result is True
            mock_get.assert_called_once_with("ENG-123")
            mock_execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_issue_failure(self, client):
        """Test issue deletion failure."""
        mock_response = {"issueArchive": {"success": False}}

        with patch.object(
            client, "execute_query", new_callable=AsyncMock
        ) as mock_execute:
            mock_execute.return_value = mock_response

            result = await client.delete_issue("issue_123")

            assert result is False

    @pytest.mark.asyncio
    async def test_delete_issue_not_found(self, client):
        """Test deleting an issue that doesn't exist."""
        with patch.object(client, "get_issue", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = None

            with pytest.raises(LinearAPIError, match="Issue not found"):
                await client.delete_issue("ENG-999")


class TestLabelOperations:
    """Test suite for label operations."""

    @pytest.mark.asyncio
    async def test_get_labels_basic(self, client):
        """Test basic label listing."""
        mock_response = {
            "issueLabels": {
                "nodes": [
                    {
                        "id": "label_1",
                        "name": "bug",
                        "color": "#ff0000",
                        "description": "Bug label",
                        "team": {"id": "team_123", "key": "ENG"},
                    }
                ],
                "pageInfo": {"hasNextPage": False, "endCursor": None},
            }
        }

        with patch.object(
            client, "execute_query", new_callable=AsyncMock
        ) as mock_execute:
            mock_execute.return_value = mock_response

            result = await client.get_labels(limit=100)

            assert result == mock_response["issueLabels"]
            mock_execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_labels_with_team_filter(self, client):
        """Test label listing with team filter."""
        mock_response = {
            "issueLabels": {
                "nodes": [],
                "pageInfo": {"hasNextPage": False, "endCursor": None},
            }
        }

        with patch.object(
            client, "execute_query", new_callable=AsyncMock
        ) as mock_execute:
            mock_execute.return_value = mock_response

            await client.get_labels(team_id="team_123", limit=50)

            mock_execute.assert_called_once()

            # Check the filter was applied
            call_args = mock_execute.call_args
            variables = call_args[0][1]  # Second argument (variables)

            assert variables["first"] == 50
            assert variables["filter"] is not None

    @pytest.mark.asyncio
    async def test_create_label_success(self, client):
        """Test successful label creation."""
        mock_response = {
            "issueLabelCreate": {
                "success": True,
                "issueLabel": {
                    "id": "label_new",
                    "name": "feature",
                    "color": "#00ff00",
                    "description": "Feature label",
                },
            }
        }

        with patch.object(
            client, "execute_query", new_callable=AsyncMock
        ) as mock_execute:
            mock_execute.return_value = mock_response

            result = await client.create_label(
                name="feature",
                color="#00ff00",
                description="Feature label",
                team_id="team_123",
            )

            assert result == mock_response["issueLabelCreate"]
            mock_execute.assert_called_once()

            # Check the input data
            call_args = mock_execute.call_args
            variables = call_args[0][1]  # Second argument (variables)
            input_data = variables["input"]

            assert input_data["name"] == "feature"
            assert input_data["color"] == "#00ff00"
            assert input_data["description"] == "Feature label"
            assert input_data["teamId"] == "team_123"

    @pytest.mark.asyncio
    async def test_create_label_minimal(self, client):
        """Test label creation with minimal required fields."""
        mock_response = {
            "issueLabelCreate": {
                "success": True,
                "issueLabel": {
                    "id": "label_minimal",
                    "name": "minimal",
                    "color": "#808080",
                },
            }
        }

        with patch.object(
            client, "execute_query", new_callable=AsyncMock
        ) as mock_execute:
            mock_execute.return_value = mock_response

            result = await client.create_label(name="minimal")

            assert result == mock_response["issueLabelCreate"]

            # Check only name and default color were set
            call_args = mock_execute.call_args
            variables = call_args[0][1]  # Second argument (variables)
            input_data = variables["input"]

            assert input_data["name"] == "minimal"
            assert input_data["color"] == "#808080"
            assert "description" not in input_data
            assert "teamId" not in input_data


class TestUserOperations:
    """Test suite for user operations."""

    @pytest.mark.asyncio
    async def test_get_users_basic(self, client):
        """Test basic user listing."""
        mock_response = {
            "users": {
                "nodes": [
                    {
                        "id": "user_1",
                        "name": "john.doe",
                        "displayName": "John Doe",
                        "email": "john@example.com",
                        "active": True,
                        "admin": False,
                    }
                ],
                "pageInfo": {"hasNextPage": False, "endCursor": None},
            }
        }

        with patch.object(
            client, "execute_query", new_callable=AsyncMock
        ) as mock_execute:
            mock_execute.return_value = mock_response

            result = await client.get_users(limit=100)

            assert result == mock_response["users"]["nodes"]
            mock_execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_users_active_only(self, client):
        """Test user listing with active filter."""
        mock_response = {
            "users": {
                "nodes": [],
                "pageInfo": {"hasNextPage": False, "endCursor": None},
            }
        }

        with patch.object(
            client, "execute_query", new_callable=AsyncMock
        ) as mock_execute:
            mock_execute.return_value = mock_response

            await client.get_users(active_only=True, limit=50)

            mock_execute.assert_called_once()

            # Check the filter was applied
            call_args = mock_execute.call_args
            variables = call_args[0][1]  # Second argument (variables)

            assert variables["first"] == 50
            assert variables["filter"] is not None
