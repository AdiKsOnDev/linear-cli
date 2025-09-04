"""
Integration tests for issue CLI commands.

Tests the actual CLI command implementations with mocked API responses.
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from click.testing import CliRunner

from linear_cli.cli.app import LinearCLIContext, main


@pytest.fixture
def mock_cli_context():
    """Create a mock CLI context for testing."""
    ctx = Mock(spec=LinearCLIContext)

    # Mock config
    config = Mock()
    config.output_format = "table"
    config.no_color = False
    config.debug = False
    config.default_team_id = "team_123"
    config.default_team_key = "ENG"
    ctx.config = config

    # Mock client
    client = Mock()
    ctx.get_client.return_value = client

    return ctx, client


class TestIssueListCommand:
    """Test suite for 'linear-cli issue list' command."""

    def test_issue_list_basic(self, mock_cli_context):
        """Test basic issue list command."""
        ctx, client = mock_cli_context

        # Mock API response
        mock_issues = {
            "nodes": [
                {
                    "id": "issue_1",
                    "identifier": "ENG-123",
                    "title": "Test Issue 1",
                    "state": {"id": "state_1", "name": "To Do", "color": "#e2e2e2"},
                    "priority": 2,
                    "assignee": {"displayName": "John Doe", "name": "john.doe"},
                    "team": {"key": "ENG"},
                    "labels": {"nodes": []},
                    "updatedAt": "2024-01-01T00:00:00Z",
                }
            ],
            "pageInfo": {"hasNextPage": False},
        }

        client.get_issues = AsyncMock(return_value=mock_issues)

        with patch("src.linear-cli.cli.commands.issue.asyncio.run") as mock_run:
            mock_run.return_value = mock_issues

            runner = CliRunner()
            with patch("src.linear-cli.cli.app.cli_context", ctx):
                result = runner.invoke(main, ["issue", "list"])

        assert result.exit_code == 0
        assert "ENG-123" in result.output
        # The title might be wrapped in the table, so check for parts
        assert "Test" in result.output and "Issue" in result.output

    def test_issue_list_with_filters(self, mock_cli_context):
        """Test issue list with filtering options."""
        ctx, client = mock_cli_context

        mock_issues = {"nodes": [], "pageInfo": {"hasNextPage": False}}
        client.get_issues = AsyncMock(return_value=mock_issues)

        with patch("src.linear-cli.cli.commands.issue.asyncio.run") as mock_run:
            mock_run.return_value = mock_issues

            runner = CliRunner()
            with patch("src.linear-cli.cli.app.cli_context", ctx):
                result = runner.invoke(
                    main,
                    [
                        "issue",
                        "list",
                        "--team",
                        "ENG",
                        "--assignee",
                        "john@example.com",
                        "--state",
                        "In Progress",
                        "--priority",
                        "3",
                        "--labels",
                        "bug,urgent",
                        "--limit",
                        "25",
                    ],
                )

        assert result.exit_code == 0

        # Verify the client was called with correct parameters
        mock_run.assert_called_once()

    def test_issue_list_json_output(self, mock_cli_context):
        """Test issue list with JSON output format."""
        ctx, client = mock_cli_context
        ctx.config.output_format = "json"

        mock_issues = {
            "nodes": [{"id": "issue_1", "identifier": "ENG-123", "title": "Test Issue"}]
        }

        client.get_issues = AsyncMock(return_value=mock_issues)

        with patch("src.linear-cli.cli.commands.issue.asyncio.run") as mock_run:
            mock_run.return_value = mock_issues

            runner = CliRunner()
            with patch("src.linear-cli.cli.app.cli_context", ctx):
                result = runner.invoke(main, ["issue", "list"])

        assert result.exit_code == 0
        # Should contain JSON-formatted output
        assert "issue_1" in result.output

    def test_issue_list_error_handling(self, mock_cli_context):
        """Test issue list error handling."""
        ctx, client = mock_cli_context

        with patch("src.linear-cli.cli.commands.issue.asyncio.run") as mock_run:
            mock_run.side_effect = Exception("API Error")

            runner = CliRunner()
            with patch("src.linear-cli.cli.app.cli_context", ctx):
                result = runner.invoke(main, ["issue", "list"])

        assert result.exit_code != 0
        assert "Failed to list issues" in result.output


class TestIssueCreateCommand:
    """Test suite for 'linear-cli issue create' command."""

    def test_issue_create_basic(self, mock_cli_context):
        """Test basic issue creation."""
        ctx, client = mock_cli_context

        mock_response = {
            "success": True,
            "issue": {
                "id": "issue_new",
                "identifier": "ENG-124",
                "title": "New Test Issue",
                "description": "Test description",
            },
        }

        with patch("src.linear-cli.cli.commands.issue.asyncio.run") as mock_run:
            mock_run.return_value = mock_response

            runner = CliRunner()
            with patch("src.linear-cli.cli.app.cli_context", ctx):
                result = runner.invoke(
                    main,
                    [
                        "issue",
                        "create",
                        "New Test Issue",
                        "--description",
                        "Test description",
                    ],
                )

        assert result.exit_code == 0
        assert "Created issue: ENG-124" in result.output

    def test_issue_create_with_options(self, mock_cli_context):
        """Test issue creation with all options."""
        ctx, client = mock_cli_context

        # Mock team lookup
        mock_teams = [{"id": "team_456", "key": "DESIGN", "name": "Design Team"}]

        # Mock user lookup
        mock_users = [
            {"id": "user_789", "email": "jane@example.com", "name": "jane.doe"}
        ]

        # Mock labels lookup
        mock_labels = {
            "nodes": [
                {"id": "label_1", "name": "feature"},
                {"id": "label_2", "name": "urgent"},
            ]
        }

        mock_create_response = {
            "success": True,
            "issue": {
                "id": "issue_complex",
                "identifier": "DESIGN-45",
                "title": "Complex Issue",
            },
        }

        client.get_teams = AsyncMock(return_value=mock_teams)
        client.get_users = AsyncMock(return_value=mock_users)
        client.get_labels = AsyncMock(return_value=mock_labels)
        client.create_issue = AsyncMock(return_value=mock_create_response)

        with patch("src.linear-cli.cli.commands.issue.asyncio.run") as mock_run:
            mock_run.return_value = mock_create_response

            runner = CliRunner()
            with patch("src.linear-cli.cli.app.cli_context", ctx):
                result = runner.invoke(
                    main,
                    [
                        "issue",
                        "create",
                        "Complex Issue",
                        "--team",
                        "DESIGN",
                        "--assignee",
                        "jane@example.com",
                        "--priority",
                        "3",
                        "--labels",
                        "feature,urgent",
                        "--description",
                        "A complex test issue",
                    ],
                )

        assert result.exit_code == 0
        assert "Created issue: DESIGN-45" in result.output

    def test_issue_create_no_team_error(self, mock_cli_context):
        """Test issue creation without team configuration."""
        ctx, client = mock_cli_context
        ctx.config.default_team_id = None

        with patch("src.linear-cli.cli.commands.issue.asyncio.run") as mock_run:
            mock_run.side_effect = ValueError("No team specified")

            runner = CliRunner()
            with patch("src.linear-cli.cli.app.cli_context", ctx):
                result = runner.invoke(main, ["issue", "create", "Test Issue"])

        assert result.exit_code != 0
        assert "No team specified" in result.output

    def test_issue_create_failure(self, mock_cli_context):
        """Test issue creation failure."""
        ctx, client = mock_cli_context

        mock_response = {"success": False}

        with patch("src.linear-cli.cli.commands.issue.asyncio.run") as mock_run:
            mock_run.return_value = mock_response

            runner = CliRunner()
            with patch("src.linear-cli.cli.app.cli_context", ctx):
                result = runner.invoke(main, ["issue", "create", "Failed Issue"])

        assert result.exit_code != 0
        assert "Failed to create issue" in result.output


class TestIssueShowCommand:
    """Test suite for 'linear-cli issue show' command."""

    def test_issue_show_by_id(self, mock_cli_context):
        """Test showing issue by ID."""
        ctx, client = mock_cli_context

        mock_issue = {
            "id": "issue_123",
            "identifier": "ENG-123",
            "title": "Test Issue",
            "description": "Detailed description",
            "state": {"name": "In Progress", "color": "#0052cc"},
            "priority": 3,
            "assignee": {"displayName": "John Doe"},
            "team": {"name": "Engineering", "key": "ENG"},
            "labels": {"nodes": [{"name": "bug", "color": "#ff0000"}]},
            "createdAt": "2024-01-01T00:00:00Z",
            "updatedAt": "2024-01-02T00:00:00Z",
            "comments": {"nodes": []},
        }

        with patch("src.linear-cli.cli.commands.issue.asyncio.run") as mock_run:
            mock_run.return_value = mock_issue

            runner = CliRunner()
            with patch("src.linear-cli.cli.app.cli_context", ctx):
                result = runner.invoke(main, ["issue", "show", "issue_123"])

        assert result.exit_code == 0
        assert "ENG-123" in result.output
        assert "Test Issue" in result.output
        assert "Detailed description" in result.output

    def test_issue_show_by_identifier(self, mock_cli_context):
        """Test showing issue by identifier."""
        ctx, client = mock_cli_context

        mock_issue = {"identifier": "ENG-123", "title": "Test Issue"}

        with patch("src.linear-cli.cli.commands.issue.asyncio.run") as mock_run:
            mock_run.return_value = mock_issue

            runner = CliRunner()
            with patch("src.linear-cli.cli.app.cli_context", ctx):
                result = runner.invoke(main, ["issue", "show", "ENG-123"])

        assert result.exit_code == 0
        assert "ENG-123" in result.output

    def test_issue_show_not_found(self, mock_cli_context):
        """Test showing non-existent issue."""
        ctx, client = mock_cli_context

        with patch("src.linear-cli.cli.commands.issue.asyncio.run") as mock_run:
            mock_run.return_value = None

            runner = CliRunner()
            with patch("src.linear-cli.cli.app.cli_context", ctx):
                result = runner.invoke(main, ["issue", "show", "nonexistent"])

        assert result.exit_code != 0
        assert "Issue not found" in result.output


class TestIssueUpdateCommand:
    """Test suite for 'linear-cli issue update' command."""

    def test_issue_update_basic(self, mock_cli_context):
        """Test basic issue update."""
        ctx, client = mock_cli_context

        mock_response = {
            "success": True,
            "issue": {"identifier": "ENG-123", "title": "Updated Issue Title"},
        }

        with patch("src.linear-cli.cli.commands.issue.asyncio.run") as mock_run:
            mock_run.return_value = mock_response

            runner = CliRunner()
            with patch("src.linear-cli.cli.app.cli_context", ctx):
                result = runner.invoke(
                    main,
                    ["issue", "update", "ENG-123", "--title", "Updated Issue Title"],
                )

        assert result.exit_code == 0
        assert "Updated issue: ENG-123" in result.output

    def test_issue_update_no_options(self, mock_cli_context):
        """Test issue update with no options provided."""
        ctx, client = mock_cli_context

        runner = CliRunner()
        with patch("src.linear-cli.cli.app.cli_context", ctx):
            result = runner.invoke(main, ["issue", "update", "ENG-123"])

        assert result.exit_code != 0
        assert "No update options provided" in result.output

    def test_issue_update_with_state(self, mock_cli_context):
        """Test issue update with state change."""
        ctx, client = mock_cli_context

        # Mock getting issue for team info
        mock_issue = {"id": "issue_123", "team": {"id": "team_123"}}

        # Mock teams with states
        mock_teams = [
            {
                "id": "team_123",
                "states": {"nodes": [{"id": "state_done", "name": "Done"}]},
            }
        ]

        mock_response = {
            "success": True,
            "issue": {"identifier": "ENG-123", "title": "Issue with new state"},
        }

        client.get_issue = AsyncMock(return_value=mock_issue)
        client.get_teams = AsyncMock(return_value=mock_teams)
        client.update_issue = AsyncMock(return_value=mock_response)

        with patch("src.linear-cli.cli.commands.issue.asyncio.run") as mock_run:
            mock_run.return_value = mock_response

            runner = CliRunner()
            with patch("src.linear-cli.cli.app.cli_context", ctx):
                result = runner.invoke(
                    main, ["issue", "update", "ENG-123", "--state", "Done"]
                )

        assert result.exit_code == 0
        assert "Updated issue: ENG-123" in result.output


class TestIssueDeleteCommand:
    """Test suite for 'linear-cli issue delete' command."""

    def test_issue_delete_with_confirmation(self, mock_cli_context):
        """Test issue deletion with confirmation."""
        ctx, client = mock_cli_context

        # Mock issue details for confirmation
        mock_issue = {"identifier": "ENG-123", "title": "Issue to Delete"}

        client.get_issue = AsyncMock(return_value=mock_issue)
        client.delete_issue = AsyncMock(return_value=True)

        with patch("src.linear-cli.cli.commands.issue.asyncio.run") as mock_run:
            mock_run.return_value = True

            runner = CliRunner()
            with patch("src.linear-cli.cli.app.cli_context", ctx):
                # Use --confirm to skip interactive confirmation
                result = runner.invoke(
                    main, ["issue", "delete", "ENG-123", "--confirm"]
                )

        assert result.exit_code == 0
        assert "Archived issue: ENG-123" in result.output

    def test_issue_delete_not_found(self, mock_cli_context):
        """Test deleting non-existent issue."""
        ctx, client = mock_cli_context

        with patch("src.linear-cli.cli.commands.issue.asyncio.run") as mock_run:
            mock_run.side_effect = ValueError("Issue not found: nonexistent")

            runner = CliRunner()
            with patch("src.linear-cli.cli.app.cli_context", ctx):
                result = runner.invoke(
                    main, ["issue", "delete", "nonexistent", "--confirm"]
                )

        assert result.exit_code != 0
        assert "Issue not found" in result.output

    def test_issue_delete_failure(self, mock_cli_context):
        """Test issue deletion failure."""
        ctx, client = mock_cli_context

        with patch("src.linear-cli.cli.commands.issue.asyncio.run") as mock_run:
            mock_run.return_value = False

            runner = CliRunner()
            with patch("src.linear-cli.cli.app.cli_context", ctx):
                result = runner.invoke(
                    main, ["issue", "delete", "ENG-123", "--confirm"]
                )

        assert result.exit_code != 0
        assert "Failed to archive issue" in result.output
