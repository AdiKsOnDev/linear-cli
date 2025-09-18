"""
Unit tests for project milestone commands.

Tests milestone functionality as subcommands of the project command group.
"""

from unittest.mock import AsyncMock, Mock

import pytest
from click.testing import CliRunner

from linear_cli.api.client.client import LinearClient
from linear_cli.cli.commands.project import project
from linear_cli.config.manager import LinearConfig


@pytest.fixture
def mock_config():
    """Mock LinearConfig for testing."""
    config = Mock(spec=LinearConfig)
    config.output_format = "table"
    config.no_color = False
    config.verbose = False
    config.debug = False
    config.rate_limit_delay = 0.1
    config.max_retries = 3
    return config


@pytest.fixture
def mock_client():
    """Mock LinearClient for testing."""
    client = Mock(spec=LinearClient)

    # Mock project methods
    client.get_project = AsyncMock()
    
    # Mock milestone methods
    client.get_milestones = AsyncMock()
    client.get_milestone = AsyncMock()
    client.create_milestone = AsyncMock()
    client.update_milestone = AsyncMock()
    client.delete_milestone = AsyncMock()
    client.resolve_milestone_id = AsyncMock()
    
    # Mock other methods
    client.get_teams = AsyncMock()
    client.get_users = AsyncMock()
    client.create_project = AsyncMock()
    client.create_issue = AsyncMock()

    return client


@pytest.fixture
def mock_cli_context(mock_config, mock_client):
    """Mock CliContext for testing."""
    context = Mock()
    context.config = mock_config
    context.get_client.return_value = mock_client
    return context


@pytest.fixture
def runner():
    """Click test runner."""
    return CliRunner()


class TestProjectMilestones:
    """Test project milestones command."""

    def test_list_project_milestones(self, runner, mock_cli_context):
        """Test listing milestones for a project."""
        # Mock project lookup
        project_data = {"id": "proj_123", "name": "Test Project"}
        mock_cli_context.get_client().get_project.return_value = project_data

        # Mock milestones response
        milestones_data = {
            "nodes": [
                {
                    "id": "milestone_123",
                    "name": "Sprint 1",
                    "description": "First sprint",
                    "targetDate": "2024-03-31T00:00:00.000Z",
                    "project": {"id": "proj_123", "name": "Test Project"},
                }
            ]
        }
        mock_cli_context.get_client().get_milestones.return_value = milestones_data

        result = runner.invoke(
            project,
            ["milestones", "Test Project"],
            obj={"cli_context": mock_cli_context},
        )

        assert result.exit_code == 0
        mock_cli_context.get_client().get_project.assert_called_once_with("Test Project")
        mock_cli_context.get_client().get_milestones.assert_called_once_with(limit=50)

    def test_list_milestones_project_not_found(self, runner, mock_cli_context):
        """Test listing milestones for non-existent project."""
        mock_cli_context.get_client().get_project.return_value = None

        result = runner.invoke(
            project,
            ["milestones", "NonExistent"],
            obj={"cli_context": mock_cli_context},
        )

        assert result.exit_code == 0
        assert "Project not found: NonExistent" in result.output


class TestShowMilestone:
    """Test show milestone command."""

    def test_show_project_milestone(self, runner, mock_cli_context):
        """Test showing milestone for a project."""
        milestone_data = {
            "id": "milestone_123",
            "name": "Sprint 1",
            "description": "First sprint",
            "targetDate": "2024-03-31T00:00:00.000Z",
            "project": {"id": "proj_123", "name": "Test Project"},
        }

        # Mock milestone resolution first
        mock_cli_context.get_client().resolve_milestone_id.return_value = "milestone_123"
        mock_cli_context.get_client().get_milestone.return_value = milestone_data

        result = runner.invoke(
            project,
            ["milestone", "Test Project", "milestone_123"],
            obj={"cli_context": mock_cli_context},
        )

        assert result.exit_code == 0
        mock_cli_context.get_client().resolve_milestone_id.assert_called_once_with("milestone_123", "Test Project")
        mock_cli_context.get_client().get_milestone.assert_called_once_with("milestone_123")

    def test_show_milestone_by_name_with_resolution(self, runner, mock_cli_context):
        """Test showing milestone by name with resolution."""
        milestone_data = {
            "id": "milestone_123",
            "name": "Sprint 1"
        }

        # Mock name resolution
        mock_cli_context.get_client().resolve_milestone_id.return_value = "milestone_123"
        mock_cli_context.get_client().get_milestone.return_value = milestone_data

        result = runner.invoke(
            project,
            ["milestone", "Test Project", "Sprint 1"],
            obj={"cli_context": mock_cli_context},
        )

        assert result.exit_code == 0
        mock_cli_context.get_client().resolve_milestone_id.assert_called_once_with("Sprint 1", "Test Project")
        mock_cli_context.get_client().get_milestone.assert_called_once_with("milestone_123")


class TestCreateMilestone:
    """Test create milestone command."""

    def test_create_project_milestone(self, runner, mock_cli_context):
        """Test creating milestone for a project."""
        # Mock project lookup
        project_data = {"id": "proj_123", "name": "Test Project"}
        mock_cli_context.get_client().get_project.return_value = project_data

        # Mock milestone creation
        create_result = {
            "success": True,
            "projectMilestone": {
                "id": "milestone_123",
                "name": "Sprint 1",
                "project": {"id": "proj_123", "name": "Test Project"},
            },
        }
        mock_cli_context.get_client().create_milestone.return_value = create_result

        result = runner.invoke(
            project,
            ["create-milestone", "Test Project", "Sprint 1"],
            obj={"cli_context": mock_cli_context},
        )

        assert result.exit_code == 0
        assert "Created milestone: Sprint 1" in result.output

        mock_cli_context.get_client().create_milestone.assert_called_once_with(
            name="Sprint 1",
            project_id="proj_123",
            description=None,
            target_date=None,
        )

    def test_create_milestone_with_options(self, runner, mock_cli_context):
        """Test creating milestone with description and target date."""
        # Mock project lookup
        project_data = {"id": "proj_123", "name": "Test Project"}
        mock_cli_context.get_client().get_project.return_value = project_data

        # Mock milestone creation
        create_result = {
            "success": True,
            "projectMilestone": {
                "id": "milestone_123",
                "name": "Sprint 1",
                "description": "Test description",
            },
        }
        mock_cli_context.get_client().create_milestone.return_value = create_result

        result = runner.invoke(
            project,
            [
                "create-milestone",
                "Test Project",
                "Sprint 1",
                "--description",
                "Test description",
                "--target-date",
                "2024-03-31",
            ],
            obj={"cli_context": mock_cli_context},
        )

        assert result.exit_code == 0

        mock_cli_context.get_client().create_milestone.assert_called_once_with(
            name="Sprint 1",
            project_id="proj_123",
            description="Test description",
            target_date="2024-03-31T00:00:00Z",
        )

    def test_create_milestone_project_not_found(self, runner, mock_cli_context):
        """Test creating milestone for non-existent project."""
        mock_cli_context.get_client().get_project.return_value = None

        result = runner.invoke(
            project,
            ["create-milestone", "NonExistent", "Sprint 1"],
            obj={"cli_context": mock_cli_context},
        )

        assert result.exit_code == 0
        assert "Project not found: NonExistent" in result.output


class TestUpdateMilestone:
    """Test update milestone command."""

    def test_update_project_milestone(self, runner, mock_cli_context):
        """Test updating milestone in a project."""
        # Mock milestone resolution
        mock_cli_context.get_client().resolve_milestone_id.return_value = "milestone_123"

        # Mock update result
        update_result = {
            "success": True,
            "projectMilestone": {
                "id": "milestone_123",
                "name": "Sprint 1 Updated",
            },
        }
        mock_cli_context.get_client().update_milestone.return_value = update_result

        result = runner.invoke(
            project,
            ["update-milestone", "Test Project", "Sprint 1", "--name", "Sprint 1 Updated"],
            obj={"cli_context": mock_cli_context},
        )

        assert result.exit_code == 0
        assert "Updated milestone: Sprint 1 Updated" in result.output

        mock_cli_context.get_client().update_milestone.assert_called_once_with(
            milestone_id="milestone_123",
            name="Sprint 1 Updated",
            description=None,
            target_date=None,
        )


class TestDeleteMilestone:
    """Test delete milestone command."""

    def test_delete_project_milestone(self, runner, mock_cli_context):
        """Test deleting milestone from a project."""
        # Mock milestone resolution
        mock_cli_context.get_client().resolve_milestone_id.return_value = "milestone_123"
        mock_cli_context.get_client().delete_milestone.return_value = True

        result = runner.invoke(
            project,
            ["delete-milestone", "Test Project", "Sprint 1"],
            obj={"cli_context": mock_cli_context},
            input="y\n",
        )

        assert result.exit_code == 0
        assert "Deleted milestone: Sprint 1" in result.output

        mock_cli_context.get_client().delete_milestone.assert_called_once_with("milestone_123")

    def test_delete_milestone_with_yes_flag(self, runner, mock_cli_context):
        """Test deleting milestone with --yes flag."""
        mock_cli_context.get_client().resolve_milestone_id.return_value = "milestone_123"
        mock_cli_context.get_client().delete_milestone.return_value = True

        result = runner.invoke(
            project,
            ["delete-milestone", "Test Project", "Sprint 1", "--yes"],
            obj={"cli_context": mock_cli_context},
        )

        assert result.exit_code == 0
        assert "Deleted milestone: Sprint 1" in result.output


class TestMilestoneIssues:
    """Test milestone issues command."""

    def test_list_milestone_issues(self, runner, mock_cli_context):
        """Test listing issues in a project milestone."""
        # Mock milestone resolution
        mock_cli_context.get_client().resolve_milestone_id.return_value = "milestone_123"

        # Mock milestone data with issues
        milestone_data = {
            "id": "milestone_123",
            "name": "Sprint 1",
            "issues": {
                "nodes": [
                    {
                        "id": "issue_123",
                        "identifier": "ENG-123",
                        "title": "Test issue",
                        "state": {"name": "In Progress"},
                    }
                ]
            },
        }
        mock_cli_context.get_client().get_milestone.return_value = milestone_data

        result = runner.invoke(
            project,
            ["milestone-issues", "Test Project", "Sprint 1"],
            obj={"cli_context": mock_cli_context},
        )

        assert result.exit_code == 0
        assert "Issues in milestone: Sprint 1" in result.output


class TestCreateTestData:
    """Test create test data command."""

    def test_create_test_data_for_project(self, runner, mock_cli_context):
        """Test creating test data for milestone testing."""
        # Mock team lookup
        teams_data = [{"id": "team_123", "key": "ENG", "name": "Engineering"}]
        mock_cli_context.get_client().get_teams.return_value = teams_data

        # Mock project creation
        project_result = {
            "success": True,
            "project": {"id": "proj_123", "name": "Test Project 1"},
        }
        mock_cli_context.get_client().create_project.return_value = project_result

        # Mock milestone creation
        milestone_result = {
            "success": True,
            "projectMilestone": {"id": "milestone_123", "name": "Milestone 1"},
        }
        mock_cli_context.get_client().create_milestone.return_value = milestone_result

        # Mock issue creation
        issue_result = {
            "success": True,
            "issue": {"id": "issue_123", "identifier": "ENG-123"},
        }
        mock_cli_context.get_client().create_issue.return_value = issue_result

        result = runner.invoke(
            project,
            ["create-test-data", "--team", "ENG"],
            obj={"cli_context": mock_cli_context},
        )

        assert result.exit_code == 0
        assert "Test data creation completed!" in result.output
        assert "Projects created: 1" in result.output
        assert "Milestones created: 3" in result.output
        assert "Issues created: 15" in result.output

    def test_create_test_data_team_not_found(self, runner, mock_cli_context):
        """Test create test data with non-existent team."""
        mock_cli_context.get_client().get_teams.return_value = []

        result = runner.invoke(
            project,
            ["create-test-data", "--team", "NONEXISTENT"],
            obj={"cli_context": mock_cli_context},
        )

        assert result.exit_code == 0
        assert "Team not found: NONEXISTENT" in result.output


class TestProjectMilestoneIntegration:
    """Test integration aspects of project milestone commands."""

    def test_project_milestone_command_hierarchy(self):
        """Test that milestone commands are properly integrated as project subcommands."""
        from linear_cli.cli.commands.project import project
        
        # Check that milestone-related commands are registered
        command_names = [cmd.name for cmd in project.commands.values()]
        expected_milestone_commands = [
            "milestones",
            "milestone", 
            "create-milestone",
            "update-milestone",
            "delete-milestone",
            "milestone-issues",
            "create-test-data"
        ]
        
        for expected in expected_milestone_commands:
            assert expected in command_names, f"Command {expected} not found in project commands"

    def test_milestone_commands_require_project_context(self):
        """Test that milestone commands properly require project context."""
        # All milestone commands should have project_id as first argument
        from linear_cli.cli.commands.project import (
            list_milestones,
            show_milestone,
            create_milestone,
            update_milestone,
            delete_milestone,
            list_milestone_issues
        )
        
        commands_with_project_arg = [
            list_milestones,
            show_milestone, 
            create_milestone,
            update_milestone,
            delete_milestone,
            list_milestone_issues
        ]
        
        for cmd in commands_with_project_arg:
            # Check that first parameter is project_id
            params = [p for p in cmd.params if hasattr(p, 'name')]
            project_params = [p for p in params if 'project' in p.name.lower()]
            assert len(project_params) > 0, f"Command {cmd.name} missing project parameter"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])