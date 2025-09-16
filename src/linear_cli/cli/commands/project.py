"""
Project management commands for Linear CLI.

Provides commands for managing projects, viewing project details,
and creating project updates.
"""

import asyncio
from typing import Any

import click
from rich.console import Console

from ..formatters import OutputFormatter, print_error

console = Console()


@click.group()
def project() -> None:
    """Project management commands."""
    pass


@project.command()
@click.option(
    "--limit",
    "-l",
    type=int,
    default=50,
    help="Maximum number of projects to list (default: 50)",
)
@click.pass_context
def list(ctx: click.Context, limit: int) -> None:
    """
    List all projects.

    Examples:
        linear project list
        linear project list --limit 10
    """
    cli_ctx = ctx.obj["cli_context"]
    client = cli_ctx.get_client()
    config = cli_ctx.config

    formatter = OutputFormatter(
        output_format=config.output_format, no_color=config.no_color
    )

    async def fetch_projects() -> dict[str, Any]:
        result = await client.get_projects(limit=limit)
        return dict(result) if isinstance(result, dict) else {}

    try:
        projects_data = asyncio.run(fetch_projects())
        formatter.format_projects(projects_data)
    except Exception as e:
        print_error(f"Failed to list projects: {e}")
        raise click.Abort() from e


@project.command()
@click.argument("project_id")
@click.pass_context
def show(ctx: click.Context, project_id: str) -> None:
    """
    Show detailed information about a project.

    PROJECT_ID can be the project ID or name.

    Examples:
        linear project show "My Project"
        linear project show project_abc123
    """
    cli_ctx = ctx.obj["cli_context"]
    client = cli_ctx.get_client()
    config = cli_ctx.config

    formatter = OutputFormatter(
        output_format=config.output_format, no_color=config.no_color
    )

    async def fetch_project() -> dict[str, Any] | None:
        result = await client.get_project(project_id)
        return dict(result) if isinstance(result, dict) else None

    try:
        project_data = asyncio.run(fetch_project())

        if not project_data:
            print_error(f"Project not found: {project_id}")
            raise click.Abort()

        formatter.format_project(project_data)
    except Exception as e:
        print_error(f"Failed to get project: {e}")
        raise click.Abort() from e


@project.command()
@click.argument("project_id")
@click.argument("content")
@click.option(
    "--health",
    type=click.Choice(["onTrack", "atRisk", "offTrack", "complete"]),
    help="Project health status",
)
@click.pass_context
def update(
    ctx: click.Context, project_id: str, content: str, health: str | None
) -> None:
    """
    Create a project update.

    PROJECT_ID can be the project ID or name.
    CONTENT is the update message.

    Examples:
        linear project update "My Project" "Made good progress this week"
        linear project update project_123 "Behind schedule" --health atRisk
    """
    cli_ctx = ctx.obj["cli_context"]
    client = cli_ctx.get_client()

    async def create_update() -> dict[str, Any]:
        result = await client.create_project_update(
            project_id=project_id, content=content, health=health
        )
        return dict(result) if isinstance(result, dict) else {}

    try:
        update_data = asyncio.run(create_update())
        console.print("[green]✓[/green] Project update created successfully")

        if update_data.get("id"):
            console.print(f"[dim]Update ID:[/dim] {update_data['id']}")

    except Exception as e:
        print_error(f"Failed to create project update: {e}")
        raise click.Abort() from e


@project.command()
@click.argument("name")
@click.option("--description", "-d", help="Project description")
@click.option(
    "--team",
    "-t",
    multiple=True,
    help="Team key or ID to associate with project (can be used multiple times)",
)
@click.option("--lead", help="Project lead email or ID (user who manages the project)")
@click.option(
    "--state",
    type=click.Choice(["planned", "started", "paused", "completed", "canceled"]),
    default="planned",
    help="Project state (default: planned)",
)
@click.option("--start-date", help="Start date (YYYY-MM-DD)")
@click.option("--target-date", help="Target completion date (YYYY-MM-DD)")
@click.pass_context
def create(
    ctx: click.Context,
    name: str,
    description: str,
    team: tuple[str, ...],
    lead: str,
    state: str,
    start_date: str,
    target_date: str,
) -> None:
    """
    Create a new project.

    Creates a project with the specified name and optional metadata.
    Use --team multiple times to associate multiple teams with the project.

    Examples:
        linear project create "My New Project"
        linear project create "Feature X" --description "New feature development"
        linear project create "Bug Fixes" --team ENG --team QA --lead john@example.com
        linear project create "Q4 Initiative" --state started --target-date 2024-12-31
        linear project create "Mobile App" --team ENG --team DESIGN --description "iOS/Android app"
    """
    cli_ctx = ctx.obj["cli_context"]
    client = cli_ctx.get_client()
    config = cli_ctx.config

    async def create_project() -> dict[str, Any]:
        # Resolve teams if provided
        team_ids = None
        if team:
            # WHY: Import constants locally to avoid circular import issues
            # These constants are only needed for this specific function
            from ...constants import TEAM_ID_MIN_LENGTH, TEAM_ID_PREFIX

            teams = await client.get_teams()
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
                    for t in teams:
                        if t.get("key") == team_identifier:
                            team_id = t["id"]
                            break

                if not team_id:
                    raise ValueError(f"Team not found: {team_identifier}")

                team_ids.append(team_id)

        # Resolve lead if provided
        lead_id = None
        if lead:
            if "@" in lead:
                # Email - look up user ID
                users = await client.get_users()
                for user in users:
                    if user.get("email") == lead:
                        lead_id = user["id"]
                        break
                if not lead_id:
                    raise ValueError(f"User not found: {lead}")
            else:
                # Assume it's a user ID
                lead_id = lead

        create_result = await client.create_project(
            name=name,
            description=description,
            team_ids=team_ids,
            lead_id=lead_id,
            state=state,
            start_date=start_date,
            target_date=target_date,
        )
        return dict(create_result) if isinstance(create_result, dict) else {}

    try:
        result = asyncio.run(create_project())

        if result.get("success"):
            project = result.get("project", {})
            project_name = project.get("name", name)
            from ..formatters import print_success

            print_success(f"Created project: {project_name}")

            # Show project details
            formatter = OutputFormatter(
                output_format=config.output_format, no_color=config.no_color
            )
            formatter.format_project(project)
        else:
            print_error("Failed to create project")
            raise click.Abort()

    except Exception as e:
        print_error(f"Failed to create project: {e}")
        if config.debug:
            console.print_exception()
        raise click.Abort() from None


@project.command()
@click.argument("project_id")
@click.option(
    "--limit",
    "-l",
    type=int,
    default=20,
    help="Maximum number of updates to show (default: 20)",
)
@click.pass_context
def updates(ctx: click.Context, project_id: str, limit: int) -> None:
    """
    List project updates.

    PROJECT_ID can be the project ID or name.

    Examples:
        linear project updates "My Project"
        linear project updates project_123 --limit 10
    """
    cli_ctx = ctx.obj["cli_context"]
    client = cli_ctx.get_client()
    config = cli_ctx.config

    formatter = OutputFormatter(
        output_format=config.output_format, no_color=config.no_color
    )

    async def fetch_updates() -> dict[str, Any]:
        result = await client.get_project_updates(project_id=project_id, limit=limit)
        return dict(result) if isinstance(result, dict) else {}

    try:
        updates_data = asyncio.run(fetch_updates())
        formatter.format_project_updates(updates_data)
    except Exception as e:
        print_error(f"Failed to get project updates: {e}")
        raise click.Abort() from e
