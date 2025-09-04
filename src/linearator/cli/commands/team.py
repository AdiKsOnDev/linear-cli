"""
Team management commands for Linearator CLI.

Handles team listing, switching, and team information display.
"""

import asyncio

import click
from rich.console import Console
from rich.table import Table

console = Console()


@click.group()
def team_group() -> None:
    """Team management commands."""
    pass


@team_group.command()
@click.option("--private", is_flag=True, help="Show only private teams")
@click.option("--public", is_flag=True, help="Show only public teams")
@click.pass_context
def list(ctx: click.Context, private: bool, public: bool) -> None:
    """
    List accessible teams.

    Shows all teams you have access to with their basic information
    including team key, name, and member/issue counts.
    """
    cli_ctx = ctx.obj["cli_context"]
    client = cli_ctx.get_client()

    console.print("Fetching teams...")

    async def fetch_teams() -> list:
        return await client.get_teams()

    try:
        teams = asyncio.run(fetch_teams())

        if not teams:
            console.print("[yellow]No teams found.[/yellow]")
            return

        # Filter teams if requested
        if private and not public:
            teams = [t for t in teams if t.get("private", False)]
        elif public and not private:
            teams = [t for t in teams if not t.get("private", False)]

        if not teams:
            filter_type = "private" if private else "public"
            console.print(f"[yellow]No {filter_type} teams found.[/yellow]")
            return

        # Display teams in a table
        table = Table(show_header=True, header_style="bold blue")
        table.add_column("Key", style="cyan", width=8)
        table.add_column("Name", style="bold")
        table.add_column("Description", style="dim")
        table.add_column("Issues", justify="right", style="green")
        table.add_column("Members", justify="right", style="blue")
        table.add_column("Type", justify="center", style="dim")

        # Sort teams by name
        teams_sorted = sorted(teams, key=lambda x: x.get("name", ""))

        for team in teams_sorted:
            team_type = "Private" if team.get("private", False) else "Public"
            description = team.get("description", "")
            if description and len(description) > 50:
                description = description[:47] + "..."

            table.add_row(
                team.get("key", ""),
                team.get("name", ""),
                description,
                str(team.get("issueCount", 0)),
                str(team.get("memberCount", 0)),
                team_type,
            )

        console.print(table)
        console.print(f"\n[dim]Found {len(teams)} team(s)[/dim]")

    except Exception as e:
        console.print(f"[red]Failed to fetch teams: {e}[/red]")
        if cli_ctx.config.debug:
            console.print_exception()
        raise click.Abort() from None


@team_group.command()
@click.argument("team_identifier")
@click.pass_context
def info(ctx: click.Context, team_identifier: str) -> None:
    """
    Show detailed information about a team.

    TEAM_IDENTIFIER can be either the team key (e.g., 'ENG') or team ID.
    """
    console.print(
        f"[dim]Team info for '{team_identifier}' will be implemented in Iteration 2[/dim]"
    )


@team_group.command()
@click.argument("team_identifier")
@click.pass_context
def switch(ctx: click.Context, team_identifier: str) -> None:
    """
    Switch default team context.

    TEAM_IDENTIFIER can be either the team key (e.g., 'ENG') or team ID.
    This sets the default team for subsequent commands.
    """
    cli_ctx = ctx.obj["cli_context"]

    # Validate team exists
    client = cli_ctx.get_client()

    async def validate_team() -> dict | None:
        teams = await client.get_teams()
        for team in teams:
            if team.get("key") == team_identifier or team.get("id") == team_identifier:
                return team
        return None

    try:
        team = asyncio.run(validate_team())

        if not team:
            console.print(f"[red]Team not found: {team_identifier}[/red]")
            console.print("Use 'linearator team list' to see available teams.")
            raise click.Abort()

        # Update configuration
        if team.get("key") == team_identifier:
            # User provided key
            cli_ctx.config_manager.update_config(
                default_team_key=team_identifier, default_team_id=team["id"]
            )
        else:
            # User provided ID
            cli_ctx.config_manager.update_config(
                default_team_id=team_identifier, default_team_key=team["key"]
            )

        console.print(
            f"[green]✓ Switched to team: {team['name']} ({team['key']})[/green]"
        )

    except Exception as e:
        console.print(f"[red]Failed to switch teams: {e}[/red]")
        if cli_ctx.config.debug:
            console.print_exception()
        raise click.Abort() from None


@team_group.command()
@click.pass_context
def current(ctx: click.Context) -> None:
    """Show current default team."""
    cli_ctx = ctx.obj["cli_context"]
    config = cli_ctx.config

    if not config.default_team_id and not config.default_team_key:
        console.print("[yellow]No default team set.[/yellow]")
        console.print("Use 'linearator team switch TEAM' to set a default team.")
        return

    # Try to get current team info
    if config.default_team_id:
        console.print(f"[dim]Default team ID:[/dim] {config.default_team_id}")

    if config.default_team_key:
        console.print(f"[dim]Default team key:[/dim] {config.default_team_key}")

    # Could fetch more details here in future iterations
    console.print(
        "\n[dim]Use 'linearator team info TEAM' for detailed information.[/dim]"
    )
