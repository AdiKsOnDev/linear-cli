"""
Unit tests for label CLI commands.

Tests the label management command implementations.
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from click.testing import CliRunner

from src.linearator.cli.app import LinearCLIContext, main


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


class TestLabelListCommand:
    """Test suite for 'linearator label list' command."""

    def test_label_list_basic(self, mock_cli_context):
        """Test basic label list command."""
        ctx, client = mock_cli_context

        mock_labels = {
            "nodes": [
                {
                    "id": "label_1",
                    "name": "bug",
                    "color": "#ff0000",
                    "description": "Bug reports",
                    "team": {"key": "ENG", "name": "Engineering"},
                    "createdAt": "2024-01-01T00:00:00Z"
                },
                {
                    "id": "label_2",
                    "name": "feature",
                    "color": "#00ff00",
                    "description": "New features",
                    "team": None,  # Global label
                    "createdAt": "2024-01-01T00:00:00Z"
                }
            ]
        }

        client.get_labels = AsyncMock(return_value=mock_labels)

        with patch('src.linearator.cli.commands.label.asyncio.run') as mock_run:
            mock_run.return_value = mock_labels

            runner = CliRunner()
            with patch('src.linearator.cli.app.cli_context', ctx):
                result = runner.invoke(main, ['label', 'list'])

        assert result.exit_code == 0
        assert "bug" in result.output
        assert "feature" in result.output

    def test_label_list_with_team_filter(self, mock_cli_context):
        """Test label list with team filtering."""
        ctx, client = mock_cli_context

        # Mock team lookup
        mock_teams = [
            {"id": "team_456", "key": "DESIGN"}
        ]

        mock_labels = {"nodes": []}

        client.get_teams = AsyncMock(return_value=mock_teams)
        client.get_labels = AsyncMock(return_value=mock_labels)

        with patch('src.linearator.cli.commands.label.asyncio.run') as mock_run:
            mock_run.return_value = mock_labels

            runner = CliRunner()
            with patch('src.linearator.cli.app.cli_context', ctx):
                result = runner.invoke(main, [
                    'label', 'list',
                    '--team', 'DESIGN',
                    '--limit', '50'
                ])

        assert result.exit_code == 0

    def test_label_list_team_not_found(self, mock_cli_context):
        """Test label list with invalid team."""
        ctx, client = mock_cli_context

        client.get_teams = AsyncMock(return_value=[])  # No teams found

        with patch('src.linearator.cli.commands.label.asyncio.run') as mock_run:
            mock_run.side_effect = ValueError("Team not found: INVALID")

            runner = CliRunner()
            with patch('src.linearator.cli.app.cli_context', ctx):
                result = runner.invoke(main, [
                    'label', 'list',
                    '--team', 'INVALID'
                ])

        assert result.exit_code != 0
        assert "Team not found" in result.output

    def test_label_list_json_output(self, mock_cli_context):
        """Test label list with JSON output."""
        ctx, client = mock_cli_context
        ctx.config.output_format = "json"

        mock_labels = {
            "nodes": [
                {
                    "id": "label_1",
                    "name": "bug",
                    "color": "#ff0000"
                }
            ]
        }

        client.get_labels = AsyncMock(return_value=mock_labels)

        with patch('src.linearator.cli.commands.label.asyncio.run') as mock_run:
            mock_run.return_value = mock_labels

            runner = CliRunner()
            with patch('src.linearator.cli.app.cli_context', ctx):
                result = runner.invoke(main, ['label', 'list'])

        assert result.exit_code == 0
        # Should contain JSON-formatted output
        assert "label_1" in result.output


class TestLabelCreateCommand:
    """Test suite for 'linearator label create' command."""

    def test_label_create_basic(self, mock_cli_context):
        """Test basic label creation."""
        ctx, client = mock_cli_context

        mock_response = {
            "success": True,
            "issueLabel": {
                "id": "label_new",
                "name": "enhancement",
                "color": "#0000ff",
                "description": None
            }
        }

        client.create_label = AsyncMock(return_value=mock_response)

        with patch('src.linearator.cli.commands.label.asyncio.run') as mock_run:
            mock_run.return_value = mock_response

            runner = CliRunner()
            with patch('src.linearator.cli.app.cli_context', ctx):
                result = runner.invoke(main, [
                    'label', 'create', 'enhancement',
                    '--color', '#0000ff'
                ])

        assert result.exit_code == 0
        assert "Created label: enhancement" in result.output

    def test_label_create_with_all_options(self, mock_cli_context):
        """Test label creation with all options."""
        ctx, client = mock_cli_context

        # Mock team lookup
        mock_teams = [
            {"id": "team_456", "key": "QA"}
        ]

        mock_response = {
            "success": True,
            "issueLabel": {
                "id": "label_complex",
                "name": "testing",
                "color": "#ffff00",
                "description": "QA testing label",
                "team": {"key": "QA"}
            }
        }

        client.get_teams = AsyncMock(return_value=mock_teams)
        client.create_label = AsyncMock(return_value=mock_response)

        with patch('src.linearator.cli.commands.label.asyncio.run') as mock_run:
            mock_run.return_value = mock_response

            runner = CliRunner()
            with patch('src.linearator.cli.app.cli_context', ctx):
                result = runner.invoke(main, [
                    'label', 'create', 'testing',
                    '--color', '#ffff00',
                    '--description', 'QA testing label',
                    '--team', 'QA'
                ])

        assert result.exit_code == 0
        assert "Created label: testing" in result.output

    def test_label_create_invalid_color(self, mock_cli_context):
        """Test label creation with invalid color format."""
        ctx, client = mock_cli_context

        with patch('src.linearator.cli.commands.label.asyncio.run') as mock_run:
            mock_run.side_effect = ValueError("Color must be a hex code")

            runner = CliRunner()
            with patch('src.linearator.cli.app.cli_context', ctx):
                result = runner.invoke(main, [
                    'label', 'create', 'bad-color',
                    '--color', 'invalid-color'
                ])

        assert result.exit_code != 0
        assert "Color must be a hex code" in result.output

    def test_label_create_team_not_found(self, mock_cli_context):
        """Test label creation with invalid team."""
        ctx, client = mock_cli_context

        client.get_teams = AsyncMock(return_value=[])

        with patch('src.linearator.cli.commands.label.asyncio.run') as mock_run:
            mock_run.side_effect = ValueError("Team not found: INVALID")

            runner = CliRunner()
            with patch('src.linearator.cli.app.cli_context', ctx):
                result = runner.invoke(main, [
                    'label', 'create', 'test-label',
                    '--team', 'INVALID'
                ])

        assert result.exit_code != 0
        assert "Team not found" in result.output

    def test_label_create_failure(self, mock_cli_context):
        """Test label creation failure."""
        ctx, client = mock_cli_context

        mock_response = {"success": False}

        with patch('src.linearator.cli.commands.label.asyncio.run') as mock_run:
            mock_run.return_value = mock_response

            runner = CliRunner()
            with patch('src.linearator.cli.app.cli_context', ctx):
                result = runner.invoke(main, [
                    'label', 'create', 'failed-label'
                ])

        assert result.exit_code != 0
        assert "Failed to create label" in result.output


class TestLabelShowCommand:
    """Test suite for 'linearator label show' command."""

    def test_label_show_found(self, mock_cli_context):
        """Test showing an existing label."""
        ctx, client = mock_cli_context

        mock_labels = {
            "nodes": [
                {
                    "id": "label_1",
                    "name": "bug",
                    "color": "#ff0000",
                    "description": "Bug reports and fixes",
                    "team": {"name": "Engineering", "key": "ENG"},
                    "creator": {"displayName": "John Doe", "name": "john.doe"},
                    "createdAt": "2024-01-01T00:00:00Z",
                    "updatedAt": "2024-01-02T00:00:00Z"
                }
            ]
        }

        client.get_labels = AsyncMock(return_value=mock_labels)

        with patch('src.linearator.cli.commands.label.asyncio.run') as mock_run:
            mock_run.return_value = mock_labels["nodes"][0]

            runner = CliRunner()
            with patch('src.linearator.cli.app.cli_context', ctx):
                result = runner.invoke(main, ['label', 'show', 'bug'])

        assert result.exit_code == 0
        assert "bug" in result.output
        assert "Bug reports and fixes" in result.output
        assert "Engineering" in result.output

    def test_label_show_with_team(self, mock_cli_context):
        """Test showing label with team specification."""
        ctx, client = mock_cli_context

        # Mock team lookup
        mock_teams = [
            {"id": "team_456", "key": "DESIGN"}
        ]

        mock_labels = {
            "nodes": [
                {
                    "id": "label_design",
                    "name": "wireframe",
                    "color": "#purple",
                    "description": "Wireframe tasks",
                    "team": {"name": "Design", "key": "DESIGN"}
                }
            ]
        }

        client.get_teams = AsyncMock(return_value=mock_teams)
        client.get_labels = AsyncMock(return_value=mock_labels)

        with patch('src.linearator.cli.commands.label.asyncio.run') as mock_run:
            mock_run.return_value = mock_labels["nodes"][0]

            runner = CliRunner()
            with patch('src.linearator.cli.app.cli_context', ctx):
                result = runner.invoke(main, [
                    'label', 'show', 'wireframe',
                    '--team', 'DESIGN'
                ])

        assert result.exit_code == 0
        assert "wireframe" in result.output
        assert "Design" in result.output

    def test_label_show_not_found(self, mock_cli_context):
        """Test showing non-existent label."""
        ctx, client = mock_cli_context

        mock_labels = {"nodes": []}  # Empty results

        client.get_labels = AsyncMock(return_value=mock_labels)

        with patch('src.linearator.cli.commands.label.asyncio.run') as mock_run:
            mock_run.return_value = None

            runner = CliRunner()
            with patch('src.linearator.cli.app.cli_context', ctx):
                result = runner.invoke(main, ['label', 'show', 'nonexistent'])

        assert result.exit_code != 0
        assert "Label not found: nonexistent" in result.output

    def test_label_show_global_label(self, mock_cli_context):
        """Test showing a global (non-team) label."""
        ctx, client = mock_cli_context

        mock_labels = {
            "nodes": [
                {
                    "id": "label_global",
                    "name": "urgent",
                    "color": "#red",
                    "description": "Urgent priority",
                    "team": None,  # Global label
                    "creator": {"displayName": "Admin"},
                    "createdAt": "2024-01-01T00:00:00Z"
                }
            ]
        }

        client.get_labels = AsyncMock(return_value=mock_labels)

        with patch('src.linearator.cli.commands.label.asyncio.run') as mock_run:
            mock_run.return_value = mock_labels["nodes"][0]

            runner = CliRunner()
            with patch('src.linearator.cli.app.cli_context', ctx):
                result = runner.invoke(main, ['label', 'show', 'urgent'])

        assert result.exit_code == 0
        assert "urgent" in result.output
        assert "Global label" in result.output

    def test_label_show_error_handling(self, mock_cli_context):
        """Test label show error handling."""
        ctx, client = mock_cli_context

        with patch('src.linearator.cli.commands.label.asyncio.run') as mock_run:
            mock_run.side_effect = Exception("API Error")

            runner = CliRunner()
            with patch('src.linearator.cli.app.cli_context', ctx):
                result = runner.invoke(main, ['label', 'show', 'test'])

        assert result.exit_code != 0
        assert "Failed to get label" in result.output
