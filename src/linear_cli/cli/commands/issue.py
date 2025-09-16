"""
Issue management commands for Linearator CLI.

Handles issue CRUD operations, listing, and management.
"""

import asyncio
from typing import Any

import click
from rich.console import Console

from ...constants import TEAM_ID_MIN_LENGTH, TEAM_ID_PREFIX
from ..formatters import OutputFormatter, print_error, print_success

console = Console()


@click.group()
def issue_group() -> None:
    """Issue management commands."""
    pass


@issue_group.command()
@click.option("--team", "-t", help="Team key or ID to filter by")
@click.option("--assignee", "-a", help="Assignee email or ID to filter by")
@click.option("--state", "-s", help="Issue state to filter by")
@click.option("--labels", "-L", help="Filter by labels (comma-separated)")
@click.option(
    "--priority",
    "-p",
    type=click.Choice(["0", "1", "2", "3", "4"]),
    help="Filter by priority (0=None, 1=Low, 2=Normal, 3=High, 4=Urgent)",
)
@click.option(
    "--limit", "-l", type=int, default=50, help="Maximum number of issues to show"
)
@click.pass_context
def list(
    ctx: click.Context,
    team: str,
    assignee: str,
    state: str,
    labels: str,
    priority: str,
    limit: int,
) -> None:
    """
    List issues with optional filtering.

    Shows issues from your accessible teams with filtering options.
    Use --team to filter by team key/ID, --assignee for assignee email/ID,
    --state for workflow state, and --labels for comma-separated label names.

    Examples:
        linear-cli issue list
        linear-cli issue list --team ENG --limit 10
        linear-cli issue list --assignee john@example.com --state "In Progress"
        linear-cli issue list --labels "bug,urgent" --priority 4
    """
    cli_ctx = ctx.obj["cli_context"]
    client = cli_ctx.get_client()
    config = cli_ctx.config

    # Create formatter
    formatter = OutputFormatter(
        output_format=config.output_format, no_color=config.no_color
    )

    # Parse labels if provided
    label_list = None
    if labels:
        label_list = [label.strip() for label in labels.split(",")]

    # Parse priority if provided
    priority_int = None
    if priority:
        priority_int = int(priority)

    async def fetch_issues() -> dict[str, Any]:
        # Determine team ID/key to use
        team_id = None
        team_key = None

        if team:
            # WHY: Linear has both team IDs (long, prefixed with "team_") and team keys (short, user-friendly like "ENG")
            # We need to distinguish between them to call the correct API parameters
            # This heuristic avoids requiring users to know the difference
            if team.startswith(TEAM_ID_PREFIX) or len(team) > TEAM_ID_MIN_LENGTH:
                team_id = team
            else:
                team_key = team
        else:
            # Use default team from config
            team_id = config.default_team_id
            team_key = config.default_team_key

        issues_result = await client.get_issues(
            team_id=team_id,
            team_key=team_key,
            # WHY: Allow users to specify assignees by email OR ID for flexibility
            # Email is more user-friendly, but IDs are needed for API calls
            assignee_email=assignee if assignee and "@" in assignee else None,
            assignee_id=assignee if assignee and "@" not in assignee else None,
            state_name=state,
            labels=label_list,
            priority=priority_int,
            limit=limit,
        )
        return dict(issues_result) if isinstance(issues_result, dict) else {}

    try:
        issues_data = asyncio.run(fetch_issues())
        formatter.format_issues(issues_data)

    except Exception as e:
        print_error(f"Failed to list issues: {e}")
        if config.debug:
            console.print_exception()
        raise click.Abort() from None


@issue_group.command()
@click.argument("title")
@click.option("--description", "-d", help="Issue description")
@click.option("--assignee", "-a", help="Assignee email or ID")
@click.option("--team", "-t", help="Team key or ID")
@click.option(
    "--priority",
    "-p",
    type=click.Choice(["0", "1", "2", "3", "4"]),
    help="Issue priority (0=None, 1=Low, 2=Normal, 3=High, 4=Urgent)",
)
@click.option("--labels", "-L", help="Label names (comma-separated)")
@click.option("--project", help="Project name or ID to assign the issue to (supports both names and IDs)")
@click.pass_context
def create(
    ctx: click.Context,
    title: str,
    description: str,
    assignee: str,
    team: str,
    priority: str,
    labels: str,
    project: str,
) -> None:
    """
    Create a new issue.

    Creates a new issue with the specified title and optional metadata.
    If no team is specified, uses the default team from configuration.

    Examples:
        linear-cli issue create "Fix login bug"
        linear-cli issue create "New feature" --description "Add user profiles"
        linear-cli issue create "Bug fix" --team ENG --assignee jane@example.com --priority 3
        linear-cli issue create "Enhancement" --labels "feature,ui" --description "Improve UX"
        linear-cli issue create "Database migration" --project "Q4 Backend Work" --team ENG
        linear-cli issue create "API refactor" --project "Backend Improvements" --priority 2
    """
    cli_ctx = ctx.obj["cli_context"]
    client = cli_ctx.get_client()
    config = cli_ctx.config

    async def create_issue() -> dict[str, Any]:
        # Determine team ID
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
            # Use default team
            team_id = config.default_team_id
            if not team_id:
                raise ValueError(
                    "No team specified and no default team configured. "
                    "Use --team option or set default team with 'linear-cli team switch'"
                )

        # Resolve assignee if provided
        assignee_id = None
        if assignee:
            if "@" in assignee:
                # WHY: Linear API only accepts user IDs, not emails, but emails are more user-friendly
                # We need to resolve email addresses to user IDs through the users API
                users = await client.get_users()
                for user in users:
                    if user.get("email") == assignee:
                        assignee_id = user["id"]
                        break
                if not assignee_id:
                    raise ValueError(f"User not found: {assignee}")
            else:
                # Assume it's a user ID
                assignee_id = assignee

        # Handle labels
        label_ids = None
        if labels:
            # WHY: Users provide comma-separated label names, but Linear API requires label IDs
            # We need to resolve names to IDs and gracefully handle non-existent labels
            label_names = [label.strip() for label in labels.split(",")]
            labels_data = await client.get_labels(team_id=team_id)
            label_map = {
                label["name"]: label["id"] for label in labels_data.get("nodes", [])
            }
            label_ids = []
            for label_name in label_names:
                if label_name in label_map:
                    label_ids.append(label_map[label_name])
                else:
                    # WHY: Warn but don't fail - partial label assignment is better than complete failure
                    console.print(
                        f"[yellow]Warning: Label '{label_name}' not found, skipping[/yellow]"
                    )

        # Parse priority
        priority_int = None
        if priority:
            priority_int = int(priority)

        # Resolve project if provided
        project_id = None
        if project:
            project_data = await client.get_project(project)
            if project_data:
                project_id = project_data["id"]
            else:
                console.print(
                    f"[yellow]Warning: Project '{project}' not found, skipping project assignment[/yellow]"
                )

        create_result = await client.create_issue(
            title=title,
            description=description,
            team_id=team_id,
            assignee_id=assignee_id,
            priority=priority_int,
            label_ids=label_ids if label_ids else None,
            project_id=project_id,
        )
        return dict(create_result) if isinstance(create_result, dict) else {}

    try:
        result = asyncio.run(create_issue())

        if result.get("success"):
            issue = result.get("issue", {})
            issue_id = issue.get("identifier") or issue.get("id", "")
            print_success(f"Created issue: {issue_id}")

            # Show issue details
            formatter = OutputFormatter(
                output_format=config.output_format, no_color=config.no_color
            )
            formatter.format_issue(issue)
        else:
            print_error("Failed to create issue")
            raise click.Abort()

    except Exception as e:
        print_error(f"Failed to create issue: {e}")
        if config.debug:
            console.print_exception()
        raise click.Abort() from None


@issue_group.command()
@click.argument("issue_id")
@click.pass_context
def show(ctx: click.Context, issue_id: str) -> None:
    """
    Show detailed information about an issue.

    ISSUE_ID can be the full ID or the issue identifier (e.g., 'ENG-123').

    Examples:
        linear-cli issue show ENG-123
        linear-cli issue show team_abc123_issue_def456
    """
    cli_ctx = ctx.obj["cli_context"]
    client = cli_ctx.get_client()
    config = cli_ctx.config

    formatter = OutputFormatter(
        output_format=config.output_format, no_color=config.no_color
    )

    async def fetch_issue() -> dict[str, Any] | None:
        issue_data = await client.get_issue(issue_id)
        return dict(issue_data) if isinstance(issue_data, dict) else None

    try:
        issue = asyncio.run(fetch_issue())

        if not issue:
            print_error(f"Issue not found: {issue_id}")
            raise click.Abort()

        formatter.format_issue(issue)

    except Exception as e:
        print_error(f"Failed to get issue: {e}")
        if config.debug:
            console.print_exception()
        raise click.Abort() from None


@issue_group.command()
@click.argument("issue_id")
@click.option("--title", help="New issue title")
@click.option("--description", "-d", help="New issue description")
@click.option("--assignee", "-a", help="New assignee email or ID")
@click.option("--state", "-s", help="New issue state name")
@click.option(
    "--priority",
    "-p",
    type=click.Choice(["0", "1", "2", "3", "4"]),
    help="New issue priority (0=None, 1=Low, 2=Normal, 3=High, 4=Urgent)",
)
@click.option("--labels", "-L", help="New labels (comma-separated, replaces existing)")
@click.option("--project", help="Project name or ID to assign the issue to (supports both names and IDs)")
@click.pass_context
def update(
    ctx: click.Context,
    issue_id: str,
    title: str,
    description: str,
    assignee: str,
    state: str,
    priority: str,
    labels: str,
    project: str,
) -> None:
    """
    Update an issue.

    ISSUE_ID can be the full ID or the issue identifier (e.g., 'ENG-123').
    Only specified fields will be updated.

    Examples:
        linear-cli issue update ENG-123 --title "Updated title"
        linear-cli issue update ENG-123 --state "Done" --assignee john@example.com
        linear-cli issue update ENG-123 --priority 4 --labels "bug,critical"
        linear-cli issue update ENG-123 --description "Updated description"
        linear-cli issue update ENG-123 --project "Backend Improvements"
        linear-cli issue update ENG-123 --project "Q4 Sprint" --priority 3
    """
    cli_ctx = ctx.obj["cli_context"]
    client = cli_ctx.get_client()
    config = cli_ctx.config

    # Check if any update options were provided
    if not any([title, description, assignee, state, priority, labels, project]):
        print_error("No update options provided. Use --help to see available options.")
        raise click.Abort()

    async def update_issue() -> dict[str, Any]:
        # Resolve assignee if provided
        assignee_id = None
        if assignee:
            if "@" in assignee:
                # Email - look up user ID
                users = await client.get_users()
                for user in users:
                    if user.get("email") == assignee:
                        assignee_id = user["id"]
                        break
                if not assignee_id:
                    raise ValueError(f"User not found: {assignee}")
            else:
                assignee_id = assignee

        # Resolve state if provided
        state_id = None
        if state:
            # Get issue to find its team
            issue = await client.get_issue(issue_id)
            if not issue:
                raise ValueError(f"Issue not found: {issue_id}")

            team_id = issue.get("team", {}).get("id")
            if team_id:
                # Get team states
                teams = await client.get_teams()
                for team in teams:
                    if team.get("id") == team_id:
                        states = team.get("states", {}).get("nodes", [])
                        for s in states:
                            if s.get("name").lower() == state.lower():
                                state_id = s["id"]
                                break
                        break

                if not state_id:
                    raise ValueError(f"State not found: {state}")

        # Handle labels
        label_ids = None
        if labels:
            label_names = [label.strip() for label in labels.split(",")]
            # Get current issue to find team
            issue = await client.get_issue(issue_id)
            if not issue:
                raise ValueError(f"Issue not found: {issue_id}")

            team_id = issue.get("team", {}).get("id")
            labels_data = await client.get_labels(team_id=team_id)
            label_map = {
                label["name"]: label["id"] for label in labels_data.get("nodes", [])
            }

            label_ids = []
            for label_name in label_names:
                if label_name in label_map:
                    label_ids.append(label_map[label_name])
                else:
                    console.print(
                        f"[yellow]Warning: Label '{label_name}' not found, skipping[/yellow]"
                    )

        # Parse priority
        priority_int = None
        if priority:
            priority_int = int(priority)

        # Resolve project if provided
        project_id = None
        if project:
            project_data = await client.get_project(project)
            if project_data:
                project_id = project_data["id"]
            else:
                console.print(
                    f"[yellow]Warning: Project '{project}' not found, skipping project assignment[/yellow]"
                )

        update_result = await client.update_issue(
            issue_id=issue_id,
            title=title,
            description=description,
            assignee_id=assignee_id,
            state_id=state_id,
            priority=priority_int,
            label_ids=label_ids if label_ids else None,
            project_id=project_id,
        )
        return dict(update_result) if isinstance(update_result, dict) else {}

    try:
        result = asyncio.run(update_issue())

        if result.get("success"):
            issue = result.get("issue", {})
            issue_identifier = issue.get("identifier") or issue.get("id", "")
            print_success(f"Updated issue: {issue_identifier}")

            # Show updated issue details
            formatter = OutputFormatter(
                output_format=config.output_format, no_color=config.no_color
            )
            formatter.format_issue(issue)
        else:
            print_error("Failed to update issue")
            raise click.Abort()

    except Exception as e:
        print_error(f"Failed to update issue: {e}")
        if config.debug:
            console.print_exception()
        raise click.Abort() from None


@issue_group.command()
@click.argument("issue_id")
@click.option("--confirm", is_flag=True, help="Skip confirmation prompt")
@click.pass_context
def delete(ctx: click.Context, issue_id: str, confirm: bool) -> None:
    """
    Delete (archive) an issue.

    ISSUE_ID can be the full ID or the issue identifier (e.g., 'ENG-123').
    This will archive the issue, not permanently delete it.

    Examples:
        linear-cli issue delete ENG-123
        linear-cli issue delete ENG-123 --confirm  # Skip confirmation prompt
    """
    cli_ctx = ctx.obj["cli_context"]
    client = cli_ctx.get_client()
    config = cli_ctx.config

    async def delete_issue() -> bool:
        # Get issue details first for confirmation
        issue = await client.get_issue(issue_id)
        if not issue:
            raise ValueError(f"Issue not found: {issue_id}")

        # Confirmation prompt
        if not confirm:
            issue_title = issue.get("title", "")
            if not click.confirm(
                f"Are you sure you want to archive issue '{issue.get('identifier', issue_id)}': {issue_title}?"
            ):
                console.print("[yellow]Operation cancelled.[/yellow]")
                return False

        delete_result = await client.delete_issue(issue_id)
        return bool(delete_result)

    try:
        success = asyncio.run(delete_issue())

        if success:
            print_success(f"Archived issue: {issue_id}")
        else:
            print_error(f"Failed to archive issue: {issue_id}")
            raise click.Abort()

    except Exception as e:
        print_error(f"Failed to delete issue: {e}")
        if config.debug:
            console.print_exception()
        raise click.Abort() from None
