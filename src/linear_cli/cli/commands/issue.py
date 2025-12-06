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


# Helper Functions for Issue Resolution
# These functions reduce complexity by extracting shared logic used in create() and update() commands
#
# STATE RESOLUTION STRATEGY DOCUMENTATION:
#
# This module implements a dual input strategy for Linear workflow states that provides
# both user convenience and backward compatibility:
#
# 1. NUMERIC STATE ENUM SYSTEM (Primary Interface):
#    - Maps numbers 0-6 to standard Linear state names
#    - Provides consistent interface across teams with different naming conventions
#    - Examples: --state 0 (Canceled), --state 3 (In Progress), --state 5 (Done)
#    - Benefits: Faster typing, consistent across teams, language-independent
#
# 2. TEXT-BASED STATE MATCHING (Backward Compatibility):
#    - Accepts exact state names as they appear in Linear
#    - Case-insensitive matching for user convenience
#    - Examples: --state "todo", --state "In Review", --state "done"
#    - Benefits: Intuitive for new users, works with custom team state names
#
# ARCHITECTURE RATIONALE:
# - Numeric states provide standardization while preserving team customization flexibility
# - Text states ensure no breaking changes for existing users and scripts
# - Helper functions encapsulate complex resolution logic for maintainability
# - GraphQL query optimization reduces API calls by fetching team states once
# - Error handling provides clear user feedback with helpful suggestions
#
# BACKWARD COMPATIBILITY APPROACH:
# - All existing text-based state commands continue to work unchanged
# - New numeric system is additive, not replacing existing functionality
# - Graceful degradation with helpful error messages and tips
# - No configuration changes required for existing users


async def resolve_team_id(team: str | None, config: Any, client: Any) -> str:
    """
    Resolve team identifier to team ID.

    Handles both team keys (like "ENG") and full team IDs, with fallback to default team.
    Uses Linear's dual identification system - short keys vs long IDs.

    Args:
        team: Team key, ID, or None for default
        config: CLI configuration with default team settings
        client: Linear API client

    Returns:
        Team ID string

    Raises:
        ValueError: If team not found or no default configured
    """
    if team:
        # WHY: Linear has both team IDs (long, prefixed) and team keys (short, user-friendly)
        # This heuristic distinguishes them to call correct API parameters
        if team.startswith(TEAM_ID_PREFIX) or len(team) > TEAM_ID_MIN_LENGTH:
            return team
        else:
            # Look up team by key
            teams = await client.get_teams()
            for t in teams:
                if t.get("key") == team:
                    return str(t["id"])
            raise ValueError(f"Team not found: {team}")
    else:
        # Use default team
        team_id = config.default_team_id
        if not team_id:
            raise ValueError(
                "No team specified and no default team configured. "
                "Use --team option or set default team with 'linear-cli team switch'"
            )
        return str(team_id)


async def resolve_assignee_id(assignee: str | None, client: Any) -> str | None:
    """
    Resolve assignee email or ID to user ID.

    Linear API requires user IDs but emails are more user-friendly.
    Handles both formats with automatic email-to-ID resolution.

    Args:
        assignee: Email address, user ID, or None
        client: Linear API client

    Returns:
        User ID string or None if no assignee specified

    Raises:
        ValueError: If email provided but user not found
    """
    if not assignee:
        return None

    if "@" in assignee:
        # WHY: Linear API only accepts user IDs, not emails, but emails are more user-friendly
        # We resolve email addresses to user IDs through the users API
        users = await client.get_users()
        for user in users:
            if user.get("email") == assignee:
                return str(user["id"])
        raise ValueError(f"User not found: {assignee}")
    else:
        # Assume it's a user ID
        return assignee


async def resolve_state_id(state: str | None, team_id: str, client: Any) -> str | None:
    """
    Resolve state name or numeric enum to state ID.

    Implements dual state resolution strategy:
    - Numeric states (0-6): Maps to standard Linear state names
    - Text states: Direct name matching for backward compatibility

    This provides user-friendly numeric shortcuts while maintaining compatibility.

    Args:
        state: State name, numeric enum (0-6), or None
        team_id: Team ID to get states from
        client: Linear API client

    Returns:
        State ID string or None if no state specified

    Raises:
        ValueError: If state not found or invalid numeric value
    """
    if not state:
        return None

    # Get team states
    teams = await client.get_teams()
    for team_data in teams:
        if team_data.get("id") == team_id:
            states = team_data.get("states", {}).get("nodes", [])

            # Check if state is numeric (enum) or text
            if state.isdigit():
                # Handle numeric state enum
                state_num = int(state)
                from ...constants import STATE_MAPPINGS

                if state_num in STATE_MAPPINGS:
                    target_state_name = STATE_MAPPINGS[state_num][0]
                    # Find matching state by name
                    for s in states:
                        if s.get("name").lower() == target_state_name.lower():
                            return str(s["id"])
                    console.print(
                        f"[yellow]Warning: State '{target_state_name}' (number {state_num}) not found in this team[/yellow]"
                    )
                    return None
                else:
                    raise ValueError(
                        f"Invalid state number: {state}. Valid states: 0-6 (0=Canceled, 1=Backlog, 2=Todo, 3=In Progress, 4=In Review, 5=Done, 6=Duplicate)"
                    )
            else:
                # Handle text state (backward compatibility)
                for s in states:
                    if s.get("name").lower() == state.lower():
                        return str(s["id"])
                # Suggest numeric alternative
                console.print(
                    "[yellow]Tip: Use numeric states for easier input (e.g., --state 3 for 'In Progress')[/yellow]"
                )
            break

    raise ValueError(f"State not found: {state}")


async def resolve_label_ids(
    labels: str | None, team_id: str, client: Any
) -> list[str] | None:
    """
    Resolve comma-separated label names to label IDs.

    Users provide friendly names but Linear API requires IDs.
    Gracefully handles non-existent labels with warnings.

    Args:
        labels: Comma-separated label names or None
        team_id: Team ID to get labels from
        client: Linear API client

    Returns:
        List of label IDs or None if no labels specified
    """
    if not labels:
        return None

    # WHY: Users provide comma-separated label names, but Linear API requires label IDs
    # We resolve names to IDs and gracefully handle non-existent labels
    label_names = [label.strip() for label in labels.split(",")]
    labels_data = await client.get_labels(team_id=team_id)
    label_map = {label["name"]: label["id"] for label in labels_data.get("nodes", [])}

    label_ids = []
    for label_name in label_names:
        if label_name in label_map:
            label_ids.append(label_map[label_name])
        else:
            # WHY: Warn but don't fail - partial label assignment is better than complete failure
            console.print(
                f"[yellow]Warning: Label '{label_name}' not found, skipping[/yellow]"
            )

    return label_ids if label_ids else None


async def resolve_project_id(project: str | None, client: Any) -> str | None:
    """
    Resolve project name or ID to project ID.

    Args:
        project: Project name, ID, or None
        client: Linear API client

    Returns:
        Project ID string or None if no project specified or not found
    """
    if not project:
        return None

    project_data = await client.get_project(project)
    if project_data:
        return str(project_data["id"])
    else:
        console.print(
            f"[yellow]Warning: Project '{project}' not found, skipping project assignment[/yellow]"
        )
        return None


async def resolve_milestone_id(
    milestone: str | None, client: Any, project_id: str | None = None
) -> str | None:
    """
    Resolve milestone name or ID to milestone ID.

    Args:
        milestone: Milestone name, ID, or None
        client: Linear API client
        project_id: Optional project ID for scoped search

    Returns:
        Milestone ID string or None if no milestone specified or not found
    """
    if not milestone:
        return None

    milestone_id = await client.resolve_milestone_id(milestone, project_id)
    if milestone_id:
        return str(milestone_id)
    else:
        console.print(
            f"[yellow]Warning: Milestone '{milestone}' not found, skipping milestone assignment[/yellow]"
        )
        return None


@click.group()
def issue_group() -> None:
    """Issue management commands."""
    pass


async def get_issue_team_id(issue_id: str, client: Any) -> str:
    """
    Get team ID from an existing issue.

    Used by update operations that need the team context.

    Args:
        issue_id: Issue ID or identifier
        client: Linear API client

    Returns:
        Team ID string

    Raises:
        ValueError: If issue not found
    """
    issue = await client.get_issue(issue_id)
    if not issue:
        raise ValueError(f"Issue not found: {issue_id}")

    team_id = issue.get("team", {}).get("id")
    if not team_id:
        raise ValueError(f"Could not determine team for issue: {issue_id}")

    return str(team_id)


@issue_group.command()
@click.option("--team", "-t", help="Team key or ID to filter by")
@click.option("--assignee", "-a", help="Assignee email or ID to filter by")
@click.option(
    "--state",
    "-s",
    help="Issue state to filter by (number: 0=Canceled, 1=Backlog, 2=Todo, 3=In Progress, 4=In Review, 5=Done, 6=Duplicate)",
)
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
@click.option(
    "--created-before",
    "-cb",
    help="Filter issues created before this date (ISO 8601 format: YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)",
)
@click.option(
    "--created-after",
    "-ca",
    help="Filter issues created after this date (ISO 8601 format: YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)",
)
@click.option(
    "--updated-before",
    "-ub",
    help="Filter issues updated before this date (ISO 8601 format: YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)",
)
@click.option(
    "--updated-after",
    "-ua",
    help="Filter issues updated after this date (ISO 8601 format: YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)",
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
    created_after: str,
    created_before: str,
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
            created_before=created_before,
            created_after=created_after,
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
@click.option(
    "--state",
    "-s",
    help="Issue state (number: 0=Canceled, 1=Backlog, 2=Todo, 3=In Progress, 4=In Review, 5=Done, 6=Duplicate)",
)
@click.option(
    "--project",
    help="Project name or ID to assign the issue to (supports both names and IDs)",
)
@click.option(
    "--milestone",
    "-m",
    help="Milestone name or ID to assign the issue to",
)
@click.pass_context
def create(
    ctx: click.Context,
    title: str,
    description: str,
    assignee: str,
    team: str,
    priority: str,
    labels: str,
    state: str,
    project: str,
    milestone: str,
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
        # Resolve all issue parameters using helper functions
        team_id = await resolve_team_id(team, config, client)
        assignee_id = await resolve_assignee_id(assignee, client)
        label_ids = await resolve_label_ids(labels, team_id, client)
        project_id = await resolve_project_id(project, client)
        state_id = await resolve_state_id(state, team_id, client)
        milestone_id = await resolve_milestone_id(milestone, client, project_id)

        # Parse priority
        priority_int = None
        if priority:
            priority_int = int(priority)

        create_result = await client.create_issue(
            title=title,
            description=description,
            team_id=team_id,
            assignee_id=assignee_id,
            state_id=state_id,
            priority=priority_int,
            label_ids=label_ids if label_ids else None,
            project_id=project_id,
            milestone_id=milestone_id,
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
@click.option(
    "--state",
    "-s",
    help="New issue state (number: 0=Canceled, 1=Backlog, 2=Todo, 3=In Progress, 4=In Review, 5=Done, 6=Duplicate)",
)
@click.option(
    "--priority",
    "-p",
    type=click.Choice(["0", "1", "2", "3", "4"]),
    help="New issue priority (0=None, 1=Low, 2=Normal, 3=High, 4=Urgent)",
)
@click.option("--labels", "-L", help="New labels (comma-separated, replaces existing)")
@click.option(
    "--project",
    help="Project name or ID to assign the issue to (supports both names and IDs)",
)
@click.option(
    "--milestone",
    "-m",
    help="Milestone name or ID to assign the issue to (use 'none' to remove)",
)
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
    milestone: str,
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
    if not any(
        [title, description, assignee, state, priority, labels, project, milestone]
    ):
        print_error("No update options provided. Use --help to see available options.")
        raise click.Abort()

    async def update_issue() -> dict[str, Any]:
        # Get team ID from existing issue (needed for state and label resolution)
        team_id = await get_issue_team_id(issue_id, client)

        # Resolve all issue parameters using helper functions
        assignee_id = await resolve_assignee_id(assignee, client)
        state_id = await resolve_state_id(state, team_id, client)
        label_ids = await resolve_label_ids(labels, team_id, client)
        project_id = await resolve_project_id(project, client)

        # Handle milestone resolution (special case for 'none' to remove milestone)
        milestone_id = None
        if milestone:
            if milestone.lower() == "none":
                milestone_id = None  # This will remove the milestone assignment
            else:
                milestone_id = await resolve_milestone_id(milestone, client, project_id)

        # Parse priority
        priority_int = None
        if priority:
            priority_int = int(priority)

        update_result = await client.update_issue(
            issue_id=issue_id,
            title=title,
            description=description,
            assignee_id=assignee_id,
            state_id=state_id,
            priority=priority_int,
            label_ids=label_ids if label_ids else None,
            project_id=project_id,
            milestone_id=milestone_id if milestone else None,
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
