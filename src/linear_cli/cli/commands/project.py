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
        return await client.get_projects(limit=limit)

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
        return await client.get_project(project_id)

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
def update(ctx: click.Context, project_id: str, content: str, health: str | None) -> None:
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
        return await client.create_project_update(
            project_id=project_id,
            content=content,
            health=health
        )

    try:
        update_data = asyncio.run(create_update())
        console.print("[green]✓[/green] Project update created successfully")

        if update_data.get("id"):
            console.print(f"[dim]Update ID:[/dim] {update_data['id']}")

    except Exception as e:
        print_error(f"Failed to create project update: {e}")
        raise click.Abort() from e


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
        return await client.get_project_updates(project_id=project_id, limit=limit)

    try:
        updates_data = asyncio.run(fetch_updates())
        formatter.format_project_updates(updates_data)
    except Exception as e:
        print_error(f"Failed to get project updates: {e}")
        raise click.Abort() from e
