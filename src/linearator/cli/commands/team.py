"""
Team management commands for Linearator CLI.

Handles team listing, switching, and team information display.
"""

import asyncio
import builtins
from typing import Any

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

    async def fetch_teams() -> builtins.list[dict[str, Any]]:
        teams_data = await client.get_teams()
        return teams_data if teams_data else []

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
    cli_ctx = ctx.obj["cli_context"]
    client = cli_ctx.get_client()
    config = cli_ctx.config

    async def fetch_team_info() -> dict[str, Any] | None:
        # First get all teams to find the matching one
        teams = await client.get_teams()
        team = None

        for t in teams:
            if t.get("key") == team_identifier or t.get("id") == team_identifier:
                team = t
                break

        if not team:
            return None

        # Get detailed team info including members
        team_id = team["id"]

        # Use the detailed team query to get members and states
        from ...api.queries import GET_TEAM_QUERY

        result = await client.execute_query(GET_TEAM_QUERY, {"id": team_id})
        team_data = result.get("team")
        return team_data if isinstance(team_data, dict) else None

    try:
        team = asyncio.run(fetch_team_info())

        if not team:
            console.print(f"[red]Team not found: {team_identifier}[/red]")
            console.print("Use 'linearator team list' to see available teams.")
            raise click.Abort()

        # Display team information
        console.print(
            f"[bold cyan]{team.get('name', '')}[/bold cyan] ([green]{team.get('key', '')}[/green])"
        )
        console.print()

        # Basic info
        description = team.get("description", "")
        if description:
            console.print(f"[dim]Description:[/dim] {description}")

        team_type = "Private" if team.get("private", False) else "Public"
        console.print(f"[dim]Type:[/dim] {team_type}")

        # Organization
        org = team.get("organization", {})
        if org:
            console.print(f"[dim]Organization:[/dim] {org.get('name', '')}")

        # Counts
        console.print(f"[dim]Issues:[/dim] {team.get('issueCount', 0)}")
        console.print(f"[dim]Members:[/dim] {team.get('memberCount', 0)}")

        # Workflow states
        states = team.get("states", {}).get("nodes", [])
        if states:
            console.print()
            console.print("[dim]Workflow States:[/dim]")

            # Sort states by position
            states_sorted = sorted(states, key=lambda x: x.get("position", 0))

            state_table = Table(show_header=True, header_style="bold blue", box=None)
            state_table.add_column("Name", style="bold")
            state_table.add_column("Type", style="dim")
            state_table.add_column("Color", justify="center")

            for state in states_sorted:
                from rich.text import Text

                color = state.get("color", "#808080")
                color_display = Text("●", style=f"color({color})")

                state_table.add_row(
                    state.get("name", ""),
                    state.get("type", "").title(),
                    color_display,
                )

            console.print(state_table)

        # Team labels
        labels = team.get("labels", {}).get("nodes", [])
        if labels:
            console.print()
            console.print(f"[dim]Team Labels ({len(labels)}):[/dim]")

            label_table = Table(show_header=True, header_style="bold blue", box=None)
            label_table.add_column("Name", style="bold")
            label_table.add_column("Color", justify="center")
            label_table.add_column("Description", style="dim")

            # Sort labels by name
            labels_sorted = sorted(labels, key=lambda x: x.get("name", ""))

            for label in labels_sorted[:10]:  # Show first 10 labels
                from rich.text import Text

                color = label.get("color", "#808080")
                color_display = Text("●", style=f"color({color})")

                description = label.get("description", "")
                if len(description) > 40:
                    description = description[:37] + "..."

                label_table.add_row(
                    label.get("name", ""),
                    color_display,
                    description,
                )

            console.print(label_table)

            if len(labels) > 10:
                console.print(f"[dim]... and {len(labels) - 10} more labels[/dim]")

        # Team members
        members = team.get("members", {}).get("nodes", [])
        if members:
            console.print()
            console.print(f"[dim]Team Members ({len(members)}):[/dim]")

            member_table = Table(show_header=True, header_style="bold blue", box=None)
            member_table.add_column("Name", style="bold")
            member_table.add_column("Display Name", style="cyan")
            member_table.add_column("Email", style="dim")
            member_table.add_column("Status", justify="center")

            # Sort members by name
            members_sorted = sorted(members, key=lambda x: x.get("name", ""))

            for member in members_sorted[:15]:  # Show first 15 members
                from rich.text import Text

                status = "Active" if member.get("active", False) else "Inactive"
                status_style = "green" if member.get("active", False) else "red"

                member_table.add_row(
                    member.get("name", ""),
                    member.get("displayName", ""),
                    member.get("email", ""),
                    Text(status, style=status_style),
                )

            console.print(member_table)

            if len(members) > 15:
                console.print(f"[dim]... and {len(members) - 15} more members[/dim]")

    except Exception as e:
        console.print(f"[red]Failed to get team info: {e}[/red]")
        if config.debug:
            console.print_exception()
        raise click.Abort() from None


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

    async def validate_team() -> dict[str, Any] | None:
        teams = await client.get_teams()
        for team in teams:
            if team.get("key") == team_identifier or team.get("id") == team_identifier:
                return dict(team) if isinstance(team, dict) else None
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
