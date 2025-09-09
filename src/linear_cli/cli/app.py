"""
Main CLI application for Linear CLI.

Provides the primary entry point and command structure using Click.
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Any

import click
from rich.console import Console
from rich.logging import RichHandler

from .. import __version__
from ..api.auth import LinearAuthenticator
from ..api.client import LinearClient
from ..config.manager import ConfigManager, LinearConfig
from ..constants import TEAM_ID_MIN_LENGTH, TEAM_ID_PREFIX
from .commands import (
    auth,
    bulk,
    completion,
    interactive,
    issue,
    label,
    search,
    team,
    user,
)
from .commands import config as config_cmd

# Initialize console for rich output
console = Console()


def setup_logging(verbose: bool = False, debug: bool = False) -> None:
    """Setup logging configuration."""
    # Determine log level
    if debug:
        level = logging.DEBUG
    elif verbose:
        level = logging.INFO
    else:
        level = logging.WARNING

    # Configure logging
    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(console=console, rich_tracebacks=True)],
    )

    # Suppress noisy library logs unless in debug mode
    if not debug:
        logging.getLogger("gql").setLevel(logging.WARNING)
        logging.getLogger("aiohttp").setLevel(logging.WARNING)
        logging.getLogger("httpx").setLevel(logging.WARNING)


class LinearCLIContext:
    """Context object to pass configuration and clients between commands."""

    def __init__(self) -> None:
        self.config_manager: ConfigManager | None = None
        self.config: LinearConfig | None = None
        self.authenticator: LinearAuthenticator | None = None
        self.client: LinearClient | None = None

    def initialize(self, config_overrides: dict[str, Any] | None = None) -> None:
        """Initialize the CLI context."""
        # Load configuration
        self.config_manager = ConfigManager()
        self.config = self.config_manager.load_config(config_overrides)

        # Setup logging
        setup_logging(self.config.verbose, self.config.debug)

        # Initialize authenticator
        self.authenticator = LinearAuthenticator(
            client_id=self.config.client_id,
            client_secret=self.config.client_secret,
            redirect_uri=self.config.redirect_uri,
        )

        # Initialize client (will be created on-demand)
        self.client = None

    def get_client(self) -> LinearClient:
        """Get or create Linear client."""
        if self.client is None:
            if not self.authenticator or not self.authenticator.is_authenticated:
                console.print(
                    "[red]Error: Not authenticated. Please run 'linear-cli auth login' first.[/red]"
                )
                sys.exit(1)

            if self.config is None:
                raise RuntimeError("Configuration not properly initialized")
            self.client = LinearClient(
                config=self.config,
                authenticator=self.authenticator,
            )

        return self.client


# Global context object
cli_context = LinearCLIContext()


@click.group()
@click.option(
    "--config-dir", type=click.Path(path_type=Path), help="Configuration directory path"
)
@click.option("--team", "-t", help="Default team ID or key")
@click.option(
    "--output-format",
    "-f",
    type=click.Choice(["table", "json", "yaml"]),
    help="Output format",
)
@click.option("--no-color", is_flag=True, help="Disable colored output")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.option("--debug", is_flag=True, help="Enable debug output")
@click.version_option(version=__version__)
@click.pass_context
def main(
    ctx: click.Context,
    config_dir: Path | None,
    team: str | None,
    output_format: str | None,
    no_color: bool,
    verbose: bool,
    debug: bool,
) -> None:
    """
    Linear CLI - A comprehensive CLI for Linear issue management.

    Manage Linear issues, teams, and projects from the command line with
    powerful filtering, search, and batch operations.

    Examples:
        linear-cli auth login                    # Authenticate with Linear
        linear-cli issue list                    # List issues
        linear-cli issue create "Bug fix"       # Create new issue
        linear-cli team list                     # List teams
        linear-cli search "api bug"              # Search issues

    For more information, visit: https://github.com/linear-cli/linear-cli
    """
    # Ensure context object exists
    ctx.ensure_object(dict)

    # Build configuration overrides from CLI options
    config_overrides: dict[str, Any] = {}
    if team:
        # Try to determine if it's an ID or key
        if team.startswith(TEAM_ID_PREFIX) or len(team) > TEAM_ID_MIN_LENGTH:
            config_overrides["default_team_id"] = team
        else:
            config_overrides["default_team_key"] = team

    if output_format:
        config_overrides["output_format"] = output_format

    if no_color:
        config_overrides["no_color"] = no_color

    if verbose:
        config_overrides["verbose"] = verbose

    if debug:
        config_overrides["debug"] = debug

    # Initialize CLI context
    if config_dir:
        cli_context.config_manager = ConfigManager(config_dir)

    try:
        cli_context.initialize(config_overrides)
        ctx.obj["cli_context"] = cli_context
    except Exception as e:
        console.print(f"[red]Error initializing Linear CLI: {e}[/red]")
        if debug:
            console.print_exception()
        sys.exit(1)


@main.command()
@click.pass_context
def version(ctx: click.Context) -> None:
    """Show version information."""
    from .. import __version__

    console.print(f"Linear CLI version {__version__}")


@main.command()
@click.pass_context
def status(ctx: click.Context) -> None:
    """Show authentication and configuration status."""
    cli_ctx = ctx.obj["cli_context"]

    console.print("[bold]Linearator Status[/bold]")
    console.print()

    # Configuration info
    config_info = cli_ctx.config_manager.get_config_info()
    console.print(f"[dim]Config directory:[/dim] {config_info['config_dir']}")
    console.print(f"[dim]Config file:[/dim] {config_info['config_file']}")
    console.print(f"[dim]Config file exists:[/dim] {config_info['config_file_exists']}")
    console.print()

    # Authentication status
    auth_status = cli_ctx.authenticator.is_authenticated
    console.print(f"[dim]Authenticated:[/dim] {'✓' if auth_status else '✗'}")

    if auth_status:
        token_info = cli_ctx.authenticator.get_token_info()
        console.print(
            f"[dim]Token type:[/dim] {token_info.get('token_type', 'unknown')}"
        )

        if token_info.get("expires_at"):
            expires = token_info["expires_at"]
            console.print(f"[dim]Token expires:[/dim] {expires}")
        else:
            console.print("[dim]Token expires:[/dim] Never (API key)")

        # Test API connection
        console.print()
        console.print("Testing API connection...")

        try:
            client = cli_ctx.get_client()

            async def test_connection() -> dict[str, Any]:
                result = await client.test_connection()
                return dict(result) if isinstance(result, dict) else {}

            result = asyncio.run(test_connection())

            if result["success"]:
                console.print(
                    f"[green]✓ Connected to Linear as {result['user']}[/green]"
                )
                console.print(f"[dim]Organization:[/dim] {result['organization']}")
                console.print(
                    f"[dim]Response time:[/dim] {result['response_time']:.2f}s"
                )
            else:
                console.print(f"[red]✗ Connection failed: {result['error']}[/red]")

        except Exception as e:
            console.print(f"[red]✗ Connection test failed: {e}[/red]")
    else:
        console.print(
            "[yellow]Please run 'linear-cli auth login' to authenticate.[/yellow]"
        )


# Add command groups
main.add_command(auth.auth_group, name="auth")
main.add_command(config_cmd.config_group, name="config")
main.add_command(team.team_group, name="team")
main.add_command(issue.issue_group, name="issue")
main.add_command(label.label_group, name="label")
main.add_command(bulk.bulk_group, name="bulk")
main.add_command(user.user_group, name="user")

# Add interactive mode
main.add_command(interactive.interactive, name="interactive")

# Add completion commands
main.add_command(completion.completion_group, name="completion")

# Add search functionality - use convenient alias as main command
main.add_command(search.search, name="search")
# Also add the group version for advanced features
main.add_command(search.search_group, name="search-advanced")


if __name__ == "__main__":
    main()
