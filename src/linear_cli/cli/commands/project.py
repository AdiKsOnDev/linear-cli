"""
Project management commands for Linear CLI.

Provides commands for managing projects, viewing project details,
and creating project updates.
"""

import asyncio
import secrets
from datetime import datetime
from typing import Any

import click
from rich.console import Console

from ..formatters import OutputFormatter, print_error, print_success

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


# Milestone Management Subcommands


@project.command("milestones")
@click.argument("project_id")
@click.option("--limit", "-l", type=int, default=50, help="Maximum number of milestones to show")
@click.pass_context
def list_milestones(
    ctx: click.Context, 
    project_id: str, 
    limit: int
) -> None:
    """
    List milestones for a project.
    
    PROJECT_ID can be the project ID or name.
    
    Examples:
        linear project milestones "My Project"
        linear project milestones project_123 --limit 10
    """
    cli_ctx = ctx.obj["cli_context"]
    client = cli_ctx.get_client()
    config = cli_ctx.config

    formatter = OutputFormatter(
        output_format=config.output_format, no_color=config.no_color
    )

    async def fetch_milestones() -> dict[str, Any]:
        # First resolve project
        project_data = await client.get_project(project_id)
        if not project_data:
            print_error(f"Project not found: {project_id}")
            return {}
        
        result = await client.get_milestones(
            project_id=project_data["id"],
            limit=limit
        )
        return dict(result) if isinstance(result, dict) else {}

    try:
        milestones_data = asyncio.run(fetch_milestones())
        if milestones_data:
            formatter.format_milestones(milestones_data)
    except Exception as e:
        print_error(f"Failed to list project milestones: {e}")
        raise click.Abort() from e


@project.command("milestone")
@click.argument("project_id")
@click.argument("milestone_id")
@click.pass_context
def show_milestone(ctx: click.Context, project_id: str, milestone_id: str) -> None:
    """
    Show milestone details for a project.
    
    PROJECT_ID can be the project ID or name.
    MILESTONE_ID can be the milestone ID or name.
    
    Examples:
        linear project milestone "My Project" "Sprint 1"
        linear project milestone project_123 milestone_456
    """
    cli_ctx = ctx.obj["cli_context"]
    client = cli_ctx.get_client()
    config = cli_ctx.config

    formatter = OutputFormatter(
        output_format=config.output_format, no_color=config.no_color
    )

    async def fetch_milestone() -> dict[str, Any] | None:
        # First try direct lookup
        milestone_data = await client.get_milestone(milestone_id)
        if not milestone_data:
            # Try resolving by name within project context
            resolved_id = await client.resolve_milestone_id(milestone_id, project_id)
            if resolved_id:
                milestone_data = await client.get_milestone(resolved_id)
        
        return dict(milestone_data) if milestone_data else None

    try:
        milestone_data = asyncio.run(fetch_milestone())
        if not milestone_data:
            print_error(f"Milestone not found: {milestone_id}")
            raise click.Abort()
        
        formatter.format_milestone(milestone_data)
    except Exception as e:
        print_error(f"Failed to get milestone: {e}")
        raise click.Abort() from e


@project.command("create-milestone")
@click.argument("project_id")
@click.argument("name")
@click.option("--description", "-d", help="Milestone description")
@click.option("--target-date", help="Target completion date (YYYY-MM-DD)")
@click.pass_context
def create_milestone(
    ctx: click.Context, project_id: str, name: str, description: str | None, target_date: str | None
) -> None:
    """
    Create a new milestone for a project.
    
    PROJECT_ID can be the project ID or name.
    
    Examples:
        linear project create-milestone "My Project" "Sprint 1"
        linear project create-milestone project_123 "Sprint 2" --description "Q2 goals"
        linear project create-milestone "My Project" "Release" --target-date 2024-03-31
    """
    cli_ctx = ctx.obj["cli_context"]
    client = cli_ctx.get_client()
    config = cli_ctx.config

    formatter = OutputFormatter(
        output_format=config.output_format, no_color=config.no_color
    )

    async def create_milestone_async() -> dict[str, Any]:
        # First resolve project
        project_data = await client.get_project(project_id)
        if not project_data:
            print_error(f"Project not found: {project_id}")
            return {}
        
        # Convert date format if provided
        formatted_date = None
        if target_date:
            try:
                # WHY: Convert YYYY-MM-DD to ISO 8601 format required by Linear API
                # Linear expects timestamps in ISO format with timezone
                parsed_date = datetime.strptime(target_date, "%Y-%m-%d")
                formatted_date = f"{parsed_date.strftime('%Y-%m-%d')}T00:00:00Z"
            except ValueError:
                print_error(f"Invalid date format: {target_date}. Use YYYY-MM-DD format.")
                return {}

        result = await client.create_milestone(
            name=name,
            project_id=project_data["id"],
            description=description,
            target_date=formatted_date,
        )
        return dict(result) if isinstance(result, dict) else {}

    try:
        result = asyncio.run(create_milestone_async())
        if not result:
            return
            
        if result.get("success"):
            milestone = result.get("projectMilestone", {})
            milestone_name = milestone.get("name", name)
            print_success(f"Created milestone: {milestone_name}")
            formatter.format_milestone(milestone)
        else:
            print_error("Failed to create milestone")
            raise click.Abort()
    except Exception as e:
        print_error(f"Failed to create milestone: {e}")
        raise click.Abort() from e


@project.command("update-milestone")
@click.argument("project_id")
@click.argument("milestone_id")
@click.option("--name", help="New milestone name")
@click.option("--description", help="New milestone description")
@click.option("--target-date", help="New target completion date (YYYY-MM-DD)")
@click.pass_context
def update_milestone(
    ctx: click.Context,
    project_id: str,
    milestone_id: str,
    name: str | None,
    description: str | None,
    target_date: str | None,
) -> None:
    """
    Update a milestone in a project.
    
    PROJECT_ID can be the project ID or name.
    MILESTONE_ID can be the milestone ID or name.
    
    Examples:
        linear project update-milestone "My Project" "Sprint 1" --name "Sprint 1 Updated"
        linear project update-milestone project_123 milestone_456 --target-date 2024-04-15
    """
    cli_ctx = ctx.obj["cli_context"]
    client = cli_ctx.get_client()
    config = cli_ctx.config

    formatter = OutputFormatter(
        output_format=config.output_format, no_color=config.no_color
    )

    async def update_milestone_async() -> dict[str, Any]:
        # Resolve milestone ID
        resolved_id = await client.resolve_milestone_id(milestone_id, project_id)
        if not resolved_id:
            print_error(f"Milestone not found: {milestone_id}")
            return {}

        # Convert date format if provided
        formatted_date = None
        if target_date:
            try:
                parsed_date = datetime.strptime(target_date, "%Y-%m-%d")
                formatted_date = f"{parsed_date.strftime('%Y-%m-%d')}T00:00:00Z"
            except ValueError:
                print_error(f"Invalid date format: {target_date}. Use YYYY-MM-DD format.")
                return {}

        result = await client.update_milestone(
            milestone_id=resolved_id,
            name=name,
            description=description,
            target_date=formatted_date,
        )
        return dict(result) if isinstance(result, dict) else {}

    try:
        result = asyncio.run(update_milestone_async())
        if not result:
            return
            
        if result.get("success"):
            milestone = result.get("projectMilestone", {})
            milestone_name = milestone.get("name", milestone_id)
            print_success(f"Updated milestone: {milestone_name}")
            formatter.format_milestone(milestone)
        else:
            print_error("Failed to update milestone")
            raise click.Abort()
    except Exception as e:
        print_error(f"Failed to update milestone: {e}")
        raise click.Abort() from e


@project.command("delete-milestone")
@click.argument("project_id")
@click.argument("milestone_id")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompt")
@click.pass_context
def delete_milestone(ctx: click.Context, project_id: str, milestone_id: str, yes: bool) -> None:
    """
    Delete a milestone from a project.
    
    PROJECT_ID can be the project ID or name.
    MILESTONE_ID can be the milestone ID or name.
    
    Examples:
        linear project delete-milestone "My Project" "Sprint 1"
        linear project delete-milestone project_123 milestone_456 --yes
    """
    cli_ctx = ctx.obj["cli_context"]
    client = cli_ctx.get_client()

    async def delete_milestone_async() -> bool:
        # Resolve milestone ID
        resolved_id = await client.resolve_milestone_id(milestone_id, project_id)
        if not resolved_id:
            print_error(f"Milestone not found: {milestone_id}")
            return False

        return await client.delete_milestone(resolved_id)

    try:
        if not yes:
            click.confirm(f"Are you sure you want to delete milestone '{milestone_id}'?", abort=True)
        
        success = asyncio.run(delete_milestone_async())
        if success:
            print_success(f"Deleted milestone: {milestone_id}")
        else:
            print_error(f"Failed to delete milestone: {milestone_id}")
            raise click.Abort()
    except Exception as e:
        print_error(f"Failed to delete milestone: {e}")
        raise click.Abort() from e


@project.command("milestone-issues")
@click.argument("project_id")  
@click.argument("milestone_id")
@click.option("--limit", "-l", type=int, default=50, help="Maximum number of issues to show")
@click.pass_context
def list_milestone_issues(ctx: click.Context, project_id: str, milestone_id: str, limit: int) -> None:
    """
    List issues in a project milestone.
    
    PROJECT_ID can be the project ID or name.
    MILESTONE_ID can be the milestone ID or name.
    
    Examples:
        linear project milestone-issues "My Project" "Sprint 1"
        linear project milestone-issues project_123 milestone_456 --limit 20
    """
    cli_ctx = ctx.obj["cli_context"]
    client = cli_ctx.get_client()
    config = cli_ctx.config

    formatter = OutputFormatter(
        output_format=config.output_format, no_color=config.no_color
    )

    async def fetch_milestone_issues() -> dict[str, Any] | None:
        # Resolve milestone ID
        resolved_id = await client.resolve_milestone_id(milestone_id, project_id)
        if not resolved_id:
            print_error(f"Milestone not found: {milestone_id}")
            return None

        milestone_data = await client.get_milestone(resolved_id)
        return dict(milestone_data) if milestone_data else None

    try:
        milestone_data = asyncio.run(fetch_milestone_issues())
        if not milestone_data:
            raise click.Abort()
            
        console.print(f"[bold]Issues in milestone:[/bold] {milestone_data.get('name', milestone_id)}")
        
        issues = milestone_data.get("issues", {}).get("nodes", [])
        if not issues:
            console.print("[dim]No issues found in this milestone.[/dim]")
            return
            
        # Format issues using existing formatter
        issues_data = {"nodes": issues}
        formatter.format_issues(issues_data)
        
    except Exception as e:
        print_error(f"Failed to get milestone issues: {e}")
        raise click.Abort() from e


@project.command("create-test-data")
@click.option("--team", "-t", required=True, help="Team key or ID to use for test data")
@click.option("--projects", type=int, default=1, help="Number of test projects to create")
@click.option("--milestones-per-project", type=int, default=3, help="Number of milestones per project")
@click.option("--issues-per-milestone", type=int, default=5, help="Number of issues per milestone")
@click.pass_context
def create_test_data(
    ctx: click.Context,
    team: str,
    projects: int,
    milestones_per_project: int,
    issues_per_milestone: int,
) -> None:
    """
    Create comprehensive test data for milestone testing.
    
    Creates test projects with milestones and linked issues for testing milestone functionality.
    
    Examples:
        linear project create-test-data --team ENG
        linear project create-test-data --team ENG --projects 2 --milestones-per-project 2
    """
    cli_ctx = ctx.obj["cli_context"]
    client = cli_ctx.get_client()

    async def create_test_data_async() -> dict[str, int]:
        # Find team
        teams = await client.get_teams()
        team_data = None
        
        for t in teams:
            if t.get("key") == team or t.get("id") == team:
                team_data = t
                break
                
        if not team_data:
            print_error(f"Team not found: {team}")
            return {"projects": 0, "milestones": 0, "issues": 0}

        counts = {"projects": 0, "milestones": 0, "issues": 0}
        
        with console.status("[bold green]Creating test data...") as status:
            for project_num in range(1, projects + 1):
                status.update(f"Creating project {project_num}/{projects}...")
                
                # Create project
                project_name = f"Test Project {project_num}"
                project_result = await client.create_project(
                    name=project_name,
                    description=f"Test project for milestone testing - {project_num}",
                    team_ids=[team_data["id"]],
                )
                
                if not project_result.get("success"):
                    console.print(f"[red]Failed to create project {project_name}[/red]")
                    continue
                    
                project_id = project_result["project"]["id"]
                counts["projects"] += 1
                
                # Create milestones for this project
                for milestone_num in range(1, milestones_per_project + 1):
                    status.update(f"Creating milestone {milestone_num} for project {project_num}...")
                    
                    milestone_name = f"Milestone {milestone_num}"
                    milestone_result = await client.create_milestone(
                        name=milestone_name,
                        project_id=project_id,
                        description=f"Test milestone {milestone_num} for {project_name}",
                    )
                    
                    if not milestone_result.get("success"):
                        console.print(f"[red]Failed to create milestone {milestone_name}[/red]")
                        continue
                        
                    milestone_id = milestone_result["projectMilestone"]["id"] 
                    counts["milestones"] += 1
                    
                    # Create issues for this milestone
                    for issue_num in range(1, issues_per_milestone + 1):
                        status.update(f"Creating issue {issue_num} for milestone {milestone_num}...")
                        
                        # WHY: Use secure random choice for realistic test data variety
                        # Different priorities and states make testing more realistic
                        priorities = ["No priority", "Low", "Medium", "High", "Urgent"]
                        priority = secrets.choice(priorities)
                        
                        issue_title = f"Test issue {issue_num} for {milestone_name}"
                        issue_result = await client.create_issue(
                            title=issue_title,
                            description=f"Test issue created for milestone testing",
                            team_id=team_data["id"],
                            priority=3,  # Medium priority 
                            project_id=project_id,
                            milestone_id=milestone_id,
                        )
                        
                        if issue_result.get("success"):
                            counts["issues"] += 1
        
        return counts

    try:
        console.print(f"[bold]Creating test data for team: {team}[/bold]")
        counts = asyncio.run(create_test_data_async())
        
        console.print("\n[green]✓[/green] Test data creation completed!")
        console.print(f"[dim]Projects created:[/dim] {counts['projects']}")
        console.print(f"[dim]Milestones created:[/dim] {counts['milestones']}")
        console.print(f"[dim]Issues created:[/dim] {counts['issues']}")
        
    except Exception as e:
        print_error(f"Failed to create test data: {e}")
        raise click.Abort() from e
