"""Basic CLI tests for core functionality."""

from click.testing import CliRunner

from linear_cli import __version__
from linear_cli.cli.app import main


class TestBasicCLI:
    """Test basic CLI functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_cli_help(self):
        """Test CLI help output."""
        result = self.runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "Linear CLI" in result.output

    def test_cli_version(self):
        """Test CLI version output."""
        result = self.runner.invoke(main, ["--version"])
        assert result.exit_code == 0
        assert __version__ in result.output

    def test_issue_group_help(self):
        """Test issue group help."""
        result = self.runner.invoke(main, ["issue", "--help"])
        assert result.exit_code == 0
        assert "issue management" in result.output.lower()

    def test_team_group_help(self):
        """Test team group help."""
        result = self.runner.invoke(main, ["team", "--help"])
        assert result.exit_code == 0
        assert "team management" in result.output.lower()

    def test_user_group_help(self):
        """Test user group help."""
        result = self.runner.invoke(main, ["user", "--help"])
        assert result.exit_code == 0
        assert "user management" in result.output.lower()

    def test_auth_group_help(self):
        """Test auth group help."""
        result = self.runner.invoke(main, ["auth", "--help"])
        assert result.exit_code == 0
        assert "authentication" in result.output.lower()

    def test_config_group_help(self):
        """Test config group help."""
        result = self.runner.invoke(main, ["config", "--help"])
        assert result.exit_code == 0
        assert "configuration" in result.output.lower()

    def test_search_group_help(self):
        """Test search group help."""
        result = self.runner.invoke(main, ["search", "--help"])
        assert result.exit_code == 0
        assert "search" in result.output.lower()

    def test_bulk_group_help(self):
        """Test bulk group help."""
        result = self.runner.invoke(main, ["bulk", "--help"])
        assert result.exit_code == 0
        assert "bulk" in result.output.lower()
