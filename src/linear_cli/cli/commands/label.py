"""
Label management commands for Linearator CLI.

Handles label listing, creation, and management operations.
"""

import asyncio
from typing import Any

import click
from rich.console import Console

from ...constants import (
    HEX_COLOR_LENGTH,
    HEX_COLOR_PREFIX,
    TEAM_ID_MIN_LENGTH,
    TEAM_ID_PREFIX,
)
from ..formatters import OutputFormatter, print_error, print_success

console = Console()


@click.group()
def label_group() -> None:
    """Label management commands."""
    pass


@label_group.command()
@click.option(
    "--team",
    "-t",
    multiple=True,
    help="Team key or ID to filter by (can be used multiple times)",
)
@click.option("--all-teams", is_flag=True, help="Show labels from all accessible teams")
@click.option(
    "--limit",
    "-l",
    type=int,
    default=100,
    help="Maximum number of labels to show per team",
)
@click.pass_context
def list(
    ctx: click.Context, team: tuple[str, ...], all_teams: bool, limit: int
) -> None:
    """
    List available labels.

    Shows all labels accessible to you, with optional team filtering.
    Use --team to filter by specific teams, or --all-teams to see labels from all teams.
    Multiple --team options can be used to check specific teams.

    Examples:
        linear-cli label list                           # Labels from default team
        linear-cli label list --team ENG                # Labels from ENG team
        linear-cli label list --team ENG --team QA      # Labels from ENG and QA teams
        linear-cli label list --all-teams               # Labels from all accessible teams
    """
    cli_ctx = ctx.obj["cli_context"]
    client = cli_ctx.get_client()
    config = cli_ctx.config

    # Create formatter
    formatter = OutputFormatter(
        output_format=config.output_format, no_color=config.no_color
    )

    async def fetch_labels() -> dict[str, Any]:
        if all_teams:
            # Get all teams and fetch labels for each
            teams = await client.get_teams()
            all_labels: dict[str, Any] = {
                "nodes": [],
                "pageInfo": {"hasNextPage": False},
            }

            for t in teams:
                team_labels = await client.get_labels(team_id=t["id"], limit=limit)
                if isinstance(team_labels, dict) and "nodes" in team_labels:
                    # WHY: Add team info to labels for better display context when showing labels from multiple teams
                    # This helps users understand which team each label belongs to in the output
                    all_labels["nodes"].extend(team_labels["nodes"])

            return all_labels

        elif team:
            # Handle multiple specific teams
            teams_data = await client.get_teams()
            team_ids = []

            for team_identifier in team:
                team_id = None

                # Check if it's already a team ID
                if (
                    team_identifier.startswith(TEAM_ID_PREFIX)
                    or len(team_identifier) > TEAM_ID_MIN_LENGTH
                ):
                    team_id = team_identifier
                else:
                    # Look up team by key
                    for t in teams_data:
                        if t.get("key") == team_identifier:
                            team_id = t["id"]
                            break

                if not team_id:
                    raise ValueError(f"Team not found: {team_identifier}")

                team_ids.append(team_id)

            # Fetch labels for all specified teams
            team_labels_collection: dict[str, Any] = {
                "nodes": [],
                "pageInfo": {"hasNextPage": False},
            }
            for team_id in team_ids:
                team_labels = await client.get_labels(team_id=team_id, limit=limit)
                if isinstance(team_labels, dict) and "nodes" in team_labels:
                    # WHY: Add team info to labels for better display context when showing labels from multiple teams
                    # This helps users understand which team each label belongs to in the output
                    team_info = next(
                        (t for t in teams_data if t["id"] == team_id), None
                    )
                    for label in team_labels["nodes"]:
                        if team_info:
                            label["team"] = {
                                "id": team_info["id"],
                                "name": team_info["name"],
                                "key": team_info["key"],
                            }
                    team_labels_collection["nodes"].extend(team_labels["nodes"])

            return team_labels_collection
        else:
            # Default behavior - use default team or no team filter
            team_id = (
                config.default_team_id if hasattr(config, "default_team_id") else None
            )
            labels_result = await client.get_labels(team_id=team_id, limit=limit)
            return dict(labels_result) if isinstance(labels_result, dict) else {}

    try:
        labels_data = asyncio.run(fetch_labels())
        formatter.format_labels(labels_data)

    except Exception as e:
        print_error(f"Failed to list labels: {e}")
        if config.debug:
            console.print_exception()
        raise click.Abort() from None


@label_group.command()
@click.argument("name")
@click.option("--color", "-c", default="#808080", help="Label color (hex code)")
@click.option("--description", "-d", help="Label description")
@click.option("--team", "-t", help="Team key or ID (for team-specific labels)")
@click.pass_context
def create(
    ctx: click.Context,
    name: str,
    color: str,
    description: str,
    team: str,
) -> None:
    """
    Create a new label.

    Creates a label with the specified name and optional metadata.
    If --team is provided, creates a team-specific label, otherwise creates a global label.
    """
    cli_ctx = ctx.obj["cli_context"]
    client = cli_ctx.get_client()
    config = cli_ctx.config

    async def create_label() -> dict[str, Any]:
        # Determine team ID if provided
        team_id = None
        if team:
            if team.startswith(TEAM_ID_PREFIX) or len(team) > TEAM_ID_MIN_LENGTH:
                team_id = team
            else:
                # Look up team by key
                teams = await client.get_teams()
                for t in teams:
                    if t.get("key") == team:
                        team_id = t["id"]
                        break
                if not team_id:
                    raise ValueError(f"Team not found: {team}")
        else:
            # Use default team if available
            team_id = config.default_team_id

        # Validate color format
        if not color.startswith(HEX_COLOR_PREFIX) or len(color) != HEX_COLOR_LENGTH:
            raise ValueError("Color must be a hex code (e.g., #FF0000)")

        create_result = await client.create_label(
            name=name,
            color=color,
            description=description,
            team_id=team_id,
        )
        return dict(create_result) if isinstance(create_result, dict) else {}

    try:
        result = asyncio.run(create_label())

        if result.get("success"):
            label = result.get("issueLabel", {})
            label_name = label.get("name", name)
            print_success(f"Created label: {label_name}")

            # Show label details in table format
            formatter = OutputFormatter(
                output_format=config.output_format, no_color=config.no_color
            )
            formatter.format_labels({"nodes": [label]})
        else:
            print_error("Failed to create label")
            raise click.Abort()

    except Exception as e:
        print_error(f"Failed to create label: {e}")
        if config.debug:
            console.print_exception()
        raise click.Abort() from None


@label_group.command()
@click.argument("label_name")
@click.option("--team", "-t", help="Team key or ID to search within")
@click.pass_context
def show(ctx: click.Context, label_name: str, team: str) -> None:
    """
    Show detailed information about a label.

    LABEL_NAME is the name of the label to show.
    Use --team to specify which team's labels to search.
    """
    cli_ctx = ctx.obj["cli_context"]
    client = cli_ctx.get_client()
    config = cli_ctx.config

    async def find_label() -> dict[str, Any] | None:
        # Determine team ID if provided
        team_id = None
        if team:
            if team.startswith(TEAM_ID_PREFIX) or len(team) > TEAM_ID_MIN_LENGTH:
                team_id = team
            else:
                # Look up team by key
                teams = await client.get_teams()
                for t in teams:
                    if t.get("key") == team:
                        team_id = t["id"]
                        break
                if not team_id:
                    raise ValueError(f"Team not found: {team}")

        # Get labels and find the matching one
        labels_data = await client.get_labels(team_id=team_id)
        for label in labels_data.get("nodes", []):
            if label.get("name", "").lower() == label_name.lower():
                return dict(label) if isinstance(label, dict) else None

        return None

    try:
        label = asyncio.run(find_label())

        if not label:
            print_error(f"Label not found: {label_name}")
            if team:
                console.print(f"[dim]Searched in team: {team}[/dim]")
            else:
                console.print("[dim]Try specifying a team with --team[/dim]")
            raise click.Abort()

        # Display label details
        console.print(f"[bold cyan]{label.get('name', '')}[/bold cyan]")
        console.print()

        # Basic info
        console.print(f"[dim]Color:[/dim] {label.get('color', '')}")

        description = label.get("description")
        if description:
            console.print(f"[dim]Description:[/dim] {description}")

        # Team info
        team_info = label.get("team")
        if team_info:
            console.print(
                f"[dim]Team:[/dim] {team_info.get('name', '')} ({team_info.get('key', '')})"
            )
        else:
            console.print("[dim]Team:[/dim] Global label")

        # Creator and dates
        creator = label.get("creator")
        if creator:
            creator_name = creator.get("displayName") or creator.get("name", "")
            console.print(f"[dim]Created by:[/dim] {creator_name}")

        from ..formatters import format_datetime

        console.print(f"[dim]Created:[/dim] {format_datetime(label.get('createdAt'))}")
        console.print(f"[dim]Updated:[/dim] {format_datetime(label.get('updatedAt'))}")

    except Exception as e:
        print_error(f"Failed to get label: {e}")
        if config.debug:
            console.print_exception()
        raise click.Abort() from None
