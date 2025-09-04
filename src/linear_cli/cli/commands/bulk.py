"""
Bulk operations commands for Linearator CLI.

Provides bulk operations for updating multiple issues efficiently.
"""

import asyncio
import logging

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm

from ..formatters import print_error, print_success

logger = logging.getLogger(__name__)
console = Console()


@click.group()
def bulk_group() -> None:
    """Bulk operations for multiple issues."""
    pass


@bulk_group.command()
@click.option(
    "--query", "-q", required=True, help="Search query to find issues to update"
)
@click.option("--team", "-t", help="Filter by team ID or key")
@click.option("--assignee", "-a", help="Filter by assignee email or ID")
@click.option("--state", "-s", help="Filter by current state name")
@click.option(
    "--labels",
    "-l",
    help="Filter by labels (comma-separated)",
    callback=lambda c, p, v: v.split(",") if v else None,
)
@click.option(
    "--priority",
    "-p",
    type=click.IntRange(0, 4),
    help="Filter by priority (0=None, 1=Low, 2=Normal, 3=High, 4=Urgent)",
)
@click.option(
    "--new-state",
    required=True,
    help="New state to set for all matching issues",
)
@click.option(
    "--limit",
    type=click.IntRange(1, 100),
    default=50,
    help="Maximum number of issues to update (default: 50)",
)
@click.option(
    "--dry-run", is_flag=True, help="Show what would be updated without making changes"
)
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompt")
@click.pass_context
def update_state(
    ctx: click.Context,
    query: str,
    team: str | None,
    assignee: str | None,
    state: str | None,
    labels: list[str] | None,
    priority: int | None,
    new_state: str,
    limit: int,
    dry_run: bool,
    yes: bool,
) -> None:
    """
    Bulk update issue states based on search criteria.

    \b
    Examples:
        # Update all "authentication" issues to "In Progress"
        linear-cli bulk update-state -q "authentication" --new-state "In Progress"

        # Update high-priority bugs to "Done" (dry run first)
        linear-cli bulk update-state -q "bug" --priority 3 --new-state "Done" --dry-run

        # Update team-specific issues with confirmation
        linear-cli bulk update-state -q "API timeout" --team ENG --new-state "To Do" --yes

    \b
    Safety Features:
        - Dry run mode shows changes without applying them
        - Confirmation prompt unless --yes is used
        - Limited to 100 issues per operation for safety
        - Shows detailed preview of all changes
    """
    cli_ctx = ctx.obj["cli_context"]
    client = cli_ctx.get_client()

    async def run_bulk_update() -> None:
        try:
            # First, search for matching issues
            console.print(
                f"[bold blue]Searching for issues matching: '{query}'[/bold blue]"
            )

            # Determine team and assignee parameters
            team_id = team_key = None
            if team:
                if len(team) > 10 or "-" in team or "_" in team:
                    team_id = team
                else:
                    team_key = team

            assignee_id = assignee_email = None
            if assignee:
                if "@" in assignee:
                    assignee_email = assignee
                else:
                    assignee_id = assignee

            # Search for issues
            search_results = await client.search_issues(
                query=query,
                team_id=team_id,
                team_key=team_key,
                assignee_id=assignee_id,
                assignee_email=assignee_email,
                state_name=state,
                labels=labels,
                priority=priority,
                limit=limit,
            )

            issues = search_results.get("nodes", [])

            if not issues:
                console.print(
                    "[yellow]No issues found matching the search criteria[/yellow]"
                )
                return

            console.print(f"[dim]Found {len(issues)} issue(s) to update[/dim]")
            console.print()

            # Show preview of changes
            console.print("[bold]Issues to be updated:[/bold]")
            for issue in issues:
                current_state = issue.get("state", {}).get("name", "Unknown")
                identifier = issue.get("identifier", "Unknown")
                title = issue.get("title", "No title")[:50] + (
                    "..." if len(issue.get("title", "")) > 50 else ""
                )

                console.print(
                    f"  {identifier}: {title} [{current_state}] → [bold green]{new_state}[/bold green]"
                )

            console.print()

            # Dry run mode - just show what would happen
            if dry_run:
                console.print(
                    "[bold yellow]DRY RUN MODE - No changes will be made[/bold yellow]"
                )
                console.print(
                    f"Would update {len(issues)} issue(s) to state '{new_state}'"
                )
                return

            # Confirmation prompt
            if not yes:
                if not Confirm.ask(
                    f"Update {len(issues)} issue(s) to state '{new_state}'?"
                ):
                    console.print("[yellow]Operation cancelled[/yellow]")
                    return

            # Perform bulk update
            console.print(f"[bold]Updating {len(issues)} issue(s)...[/bold]")
            success_count = 0
            error_count = 0

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("Updating issues...", total=len(issues))

                for issue in issues:
                    issue_id = issue.get("id")
                    identifier = issue.get("identifier", "Unknown")

                    try:
                        await client.update_issue(
                            issue_id=issue_id,
                            state_name=new_state,
                        )
                        success_count += 1
                        progress.update(
                            task,
                            description=f"Updated {identifier} ✓",
                            advance=1,
                        )
                    except Exception as e:
                        error_count += 1
                        logger.error(f"Failed to update {identifier}: {e}")
                        progress.update(
                            task,
                            description=f"Failed {identifier} ✗",
                            advance=1,
                        )

            # Summary
            console.print()
            if success_count > 0:
                print_success(f"Successfully updated {success_count} issue(s)")
            if error_count > 0:
                print_error(f"Failed to update {error_count} issue(s)")

        except Exception as e:
            print_error(f"Bulk update failed: {e}")

    try:
        asyncio.run(run_bulk_update())
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user[/yellow]")


@bulk_group.command()
@click.option(
    "--query", "-q", required=True, help="Search query to find issues to assign"
)
@click.option("--team", "-t", help="Filter by team ID or key")
@click.option("--state", "-s", help="Filter by state name")
@click.option(
    "--labels",
    "-l",
    help="Filter by labels (comma-separated)",
    callback=lambda c, p, v: v.split(",") if v else None,
)
@click.option(
    "--priority",
    "-p",
    type=click.IntRange(0, 4),
    help="Filter by priority (0=None, 1=Low, 2=Normal, 3=High, 4=Urgent)",
)
@click.option(
    "--assignee",
    "-a",
    required=True,
    help="User email or ID to assign all matching issues to",
)
@click.option(
    "--limit",
    type=click.IntRange(1, 100),
    default=50,
    help="Maximum number of issues to assign (default: 50)",
)
@click.option(
    "--dry-run", is_flag=True, help="Show what would be assigned without making changes"
)
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompt")
@click.pass_context
def assign(
    ctx: click.Context,
    query: str,
    team: str | None,
    state: str | None,
    labels: list[str] | None,
    priority: int | None,
    assignee: str,
    limit: int,
    dry_run: bool,
    yes: bool,
) -> None:
    """
    Bulk assign issues based on search criteria.

    \b
    Examples:
        # Assign all authentication bugs to a team member
        linear-cli bulk assign -q "auth bug" --assignee john@company.com

        # Assign high-priority issues in a team (dry run first)
        linear-cli bulk assign -q "critical" --team ENG --priority 4 --assignee lead@company.com --dry-run

        # Assign unassigned issues in "To Do" state
        linear-cli bulk assign -q "unassigned" --state "To Do" --assignee dev@company.com --yes

    \b
    Safety Features:
        - Dry run mode shows changes without applying them
        - Confirmation prompt unless --yes is used
        - Limited to 100 issues per operation for safety
        - Shows detailed preview of all assignments
    """
    cli_ctx = ctx.obj["cli_context"]
    client = cli_ctx.get_client()

    async def run_bulk_assign() -> None:
        try:
            # Search for matching issues (exclude already assigned to this user)
            console.print(
                f"[bold blue]Searching for issues to assign to {assignee}[/bold blue]"
            )

            # Determine team parameters
            team_id = team_key = None
            if team:
                if len(team) > 10 or "-" in team or "_" in team:
                    team_id = team
                else:
                    team_key = team

            # Search for issues
            search_results = await client.search_issues(
                query=query,
                team_id=team_id,
                team_key=team_key,
                state_name=state,
                labels=labels,
                priority=priority,
                limit=limit,
            )

            issues = search_results.get("nodes", [])

            if not issues:
                console.print(
                    "[yellow]No issues found matching the search criteria[/yellow]"
                )
                return

            # Filter out issues already assigned to the target user
            unassigned_issues = []
            for issue in issues:
                current_assignee = issue.get("assignee")
                current_email = (
                    current_assignee.get("email", "") if current_assignee else ""
                )
                current_id = current_assignee.get("id", "") if current_assignee else ""

                # WHY: Skip issues already assigned to target user to avoid:
                # 1. Unnecessary API calls and quota consumption
                # 2. Misleading success messages for unchanged assignments
                # 3. User confusion about actual changes made
                # This safety mechanism prevents redundant operations and improves user experience
                if assignee == current_email or assignee == current_id:
                    continue

                unassigned_issues.append(issue)

            if not unassigned_issues:
                console.print(
                    f"[yellow]All matching issues are already assigned to {assignee}[/yellow]"
                )
                return

            console.print(
                f"[dim]Found {len(unassigned_issues)} issue(s) to assign[/dim]"
            )
            console.print()

            # Show preview of assignments
            console.print("[bold]Issues to be assigned:[/bold]")
            for issue in unassigned_issues:
                current_assignee = issue.get("assignee")
                current_name = (
                    current_assignee.get("displayName", "Unassigned")
                    if current_assignee
                    else "Unassigned"
                )
                identifier = issue.get("identifier", "Unknown")
                title = issue.get("title", "No title")[:50] + (
                    "..." if len(issue.get("title", "")) > 50 else ""
                )

                console.print(
                    f"  {identifier}: {title} [{current_name}] → [bold green]{assignee}[/bold green]"
                )

            console.print()

            # Dry run mode
            if dry_run:
                console.print(
                    "[bold yellow]DRY RUN MODE - No changes will be made[/bold yellow]"
                )
                console.print(
                    f"Would assign {len(unassigned_issues)} issue(s) to {assignee}"
                )
                return

            # Confirmation prompt
            if not yes:
                if not Confirm.ask(
                    f"Assign {len(unassigned_issues)} issue(s) to {assignee}?"
                ):
                    console.print("[yellow]Operation cancelled[/yellow]")
                    return

            # Perform bulk assignment
            console.print(
                f"[bold]Assigning {len(unassigned_issues)} issue(s)...[/bold]"
            )
            success_count = 0
            error_count = 0

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task(
                    "Assigning issues...", total=len(unassigned_issues)
                )

                for issue in unassigned_issues:
                    issue_id = issue.get("id")
                    identifier = issue.get("identifier", "Unknown")

                    try:
                        # Determine assignee parameters
                        assignee_id = assignee_email = None
                        if "@" in assignee:
                            assignee_email = assignee
                        else:
                            assignee_id = assignee

                        await client.update_issue(
                            issue_id=issue_id,
                            assignee_id=assignee_id,
                            assignee_email=assignee_email,
                        )
                        success_count += 1
                        progress.update(
                            task,
                            description=f"Assigned {identifier} ✓",
                            advance=1,
                        )
                    except Exception as e:
                        error_count += 1
                        logger.error(f"Failed to assign {identifier}: {e}")
                        progress.update(
                            task,
                            description=f"Failed {identifier} ✗",
                            advance=1,
                        )

            # Summary
            console.print()
            if success_count > 0:
                print_success(f"Successfully assigned {success_count} issue(s)")
            if error_count > 0:
                print_error(f"Failed to assign {error_count} issue(s)")

        except Exception as e:
            print_error(f"Bulk assignment failed: {e}")

    try:
        asyncio.run(run_bulk_assign())
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user[/yellow]")


@bulk_group.command()
@click.option(
    "--query", "-q", required=True, help="Search query to find issues to label"
)
@click.option("--team", "-t", help="Filter by team ID or key")
@click.option("--assignee", "-a", help="Filter by assignee email or ID")
@click.option("--state", "-s", help="Filter by state name")
@click.option(
    "--priority",
    "-p",
    type=click.IntRange(0, 4),
    help="Filter by priority (0=None, 1=Low, 2=Normal, 3=High, 4=Urgent)",
)
@click.option(
    "--add-labels",
    help="Labels to add to all matching issues (comma-separated)",
    callback=lambda c, p, v: v.split(",") if v else None,
)
@click.option(
    "--remove-labels",
    help="Labels to remove from all matching issues (comma-separated)",
    callback=lambda c, p, v: v.split(",") if v else None,
)
@click.option(
    "--limit",
    type=click.IntRange(1, 100),
    default=50,
    help="Maximum number of issues to label (default: 50)",
)
@click.option(
    "--dry-run", is_flag=True, help="Show what would be labeled without making changes"
)
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompt")
@click.pass_context
def label(
    ctx: click.Context,
    query: str,
    team: str | None,
    assignee: str | None,
    state: str | None,
    priority: int | None,
    add_labels: list[str] | None,
    remove_labels: list[str] | None,
    limit: int,
    dry_run: bool,
    yes: bool,
) -> None:
    """
    Bulk add or remove labels from issues based on search criteria.

    \b
    Examples:
        # Add "urgent" label to all authentication issues
        linear-cli bulk label -q "authentication" --add-labels "urgent"

        # Remove "wip" and add "review" labels to completed issues
        linear-cli bulk label -q "completed" --remove-labels "wip" --add-labels "review"

        # Add multiple labels to high-priority bugs (dry run first)
        linear-cli bulk label -q "bug" --priority 4 --add-labels "critical,hotfix" --dry-run

    \b
    Safety Features:
        - Dry run mode shows changes without applying them
        - Confirmation prompt unless --yes is used
        - Limited to 100 issues per operation for safety
        - Shows detailed preview of all label changes
        - Must specify at least one of --add-labels or --remove-labels
    """
    if not add_labels and not remove_labels:
        raise click.UsageError(
            "Must specify at least one of --add-labels or --remove-labels"
        )

    cli_ctx = ctx.obj["cli_context"]
    client = cli_ctx.get_client()

    async def run_bulk_label() -> None:
        try:
            # Search for matching issues
            console.print(
                f"[bold blue]Searching for issues to label: '{query}'[/bold blue]"
            )

            # Determine team and assignee parameters
            team_id = team_key = None
            if team:
                if len(team) > 10 or "-" in team or "_" in team:
                    team_id = team
                else:
                    team_key = team

            assignee_id = assignee_email = None
            if assignee:
                if "@" in assignee:
                    assignee_email = assignee
                else:
                    assignee_id = assignee

            # Search for issues
            search_results = await client.search_issues(
                query=query,
                team_id=team_id,
                team_key=team_key,
                assignee_id=assignee_id,
                assignee_email=assignee_email,
                state_name=state,
                priority=priority,
                limit=limit,
            )

            issues = search_results.get("nodes", [])

            if not issues:
                console.print(
                    "[yellow]No issues found matching the search criteria[/yellow]"
                )
                return

            console.print(f"[dim]Found {len(issues)} issue(s) to update[/dim]")
            console.print()

            # Show preview of label changes
            console.print("[bold]Label changes to be made:[/bold]")
            for issue in issues:
                identifier = issue.get("identifier", "Unknown")
                title = issue.get("title", "No title")[:40] + (
                    "..." if len(issue.get("title", "")) > 40 else ""
                )
                current_labels = [
                    label["name"] for label in issue.get("labels", {}).get("nodes", [])
                ]

                changes = []
                if add_labels:
                    changes.append(f"[green]+{','.join(add_labels)}[/green]")
                if remove_labels:
                    changes.append(f"[red]-{','.join(remove_labels)}[/red]")

                console.print(f"  {identifier}: {title}")
                console.print(
                    f"    Current: {', '.join(current_labels) if current_labels else 'None'}"
                )
                console.print(f"    Changes: {' '.join(changes)}")
                console.print()

            # Dry run mode
            if dry_run:
                console.print(
                    "[bold yellow]DRY RUN MODE - No changes will be made[/bold yellow]"
                )
                console.print(f"Would update labels on {len(issues)} issue(s)")
                return

            # Confirmation prompt
            change_desc = []
            if add_labels:
                change_desc.append(f"add {','.join(add_labels)}")
            if remove_labels:
                change_desc.append(f"remove {','.join(remove_labels)}")

            if not yes:
                if not Confirm.ask(
                    f"Apply label changes ({' and '.join(change_desc)}) to {len(issues)} issue(s)?"
                ):
                    console.print("[yellow]Operation cancelled[/yellow]")
                    return

            # Perform bulk labeling
            console.print(f"[bold]Updating labels on {len(issues)} issue(s)...[/bold]")
            success_count = 0
            error_count = 0

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("Updating labels...", total=len(issues))

                for issue in issues:
                    issue_id = issue.get("id")
                    identifier = issue.get("identifier", "Unknown")

                    try:
                        # Get current label names
                        current_label_names = [
                            label["name"]
                            for label in issue.get("labels", {}).get("nodes", [])
                        ]

                        # Calculate new labels
                        new_labels = set(current_label_names)

                        if add_labels:
                            new_labels.update(add_labels)

                        if remove_labels:
                            new_labels = new_labels - set(remove_labels)

                        # Only update if labels changed
                        if set(current_label_names) != new_labels:
                            await client.update_issue(
                                issue_id=issue_id,
                                labels=list(new_labels),
                            )

                        success_count += 1
                        progress.update(
                            task,
                            description=f"Updated {identifier} ✓",
                            advance=1,
                        )
                    except Exception as e:
                        error_count += 1
                        logger.error(f"Failed to update labels for {identifier}: {e}")
                        progress.update(
                            task,
                            description=f"Failed {identifier} ✗",
                            advance=1,
                        )

            # Summary
            console.print()
            if success_count > 0:
                print_success(
                    f"Successfully updated labels on {success_count} issue(s)"
                )
            if error_count > 0:
                print_error(f"Failed to update {error_count} issue(s)")

        except Exception as e:
            print_error(f"Bulk labeling failed: {e}")

    try:
        asyncio.run(run_bulk_label())
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user[/yellow]")
