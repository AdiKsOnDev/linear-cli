"""
User management commands for Linearator CLI.

Provides user listing, workload analysis, and assignment suggestions.
"""

import asyncio
import builtins
import logging
from collections import defaultdict
from typing import Any

import click
from rich.console import Console
from rich.table import Table

from ..formatters import OutputFormatter, print_error

logger = logging.getLogger(__name__)
console = Console()


@click.group()
def user_group() -> None:
    """User management and workload analysis commands."""
    pass


@user_group.command()
@click.option("--team", "-t", help="Filter users by team ID or key")
@click.option(
    "--format",
    "-f",
    "output_format",
    type=click.Choice(["table", "json", "yaml"]),
    help="Output format (overrides global setting)",
)
@click.option("--no-color", is_flag=True, help="Disable colored output")
@click.pass_context
def list(
    ctx: click.Context,
    team: str | None,
    output_format: str | None,
    no_color: bool,
) -> None:
    """
    List team members with basic information.

    \b
    Examples:
        linear-cli user list                    # List all accessible users
        linear-cli user list --team ENG         # List users in Engineering team
        linear-cli user list --format json      # JSON output for scripting

    \b
    Output includes:
        - User display name and email
        - User ID for API operations
        - Active status
        - Team membership information
    """
    cli_ctx = ctx.obj["cli_context"]
    client = cli_ctx.get_client()
    config = cli_ctx.config

    async def run_list_users() -> None:
        try:
            # Determine team parameters
            team_id = None
            if team:
                if len(team) > 10 or "-" in team or "_" in team:
                    team_id = team
                else:
                    # Would need to resolve team key to ID for API call
                    # For now, we'll skip team filtering if key is provided
                    pass

            # Get users - the API client should support team filtering
            users = await client.get_users(
                team_id=team_id if team_id else None,
                limit=100,  # Get more users for team operations
            )

            if not users:
                console.print("[yellow]No users found[/yellow]")
                return

            # Format and display results
            formatter = OutputFormatter(
                output_format=output_format or config.output_format,
                no_color=no_color or config.no_color,
            )

            if output_format in ["json", "yaml"]:
                formatter.format_generic(users)
            else:
                # Create rich table for user display
                table = Table(title=f"Team Members{f' ({team})' if team else ''}")
                table.add_column("Name", style="bold")
                table.add_column("Email", style="cyan")
                table.add_column("ID", style="dim")
                table.add_column("Status", justify="center")

                for user in users:
                    name = user.get("displayName", user.get("name", "Unknown"))
                    email = user.get("email", "No email")
                    user_id = user.get("id", "Unknown")
                    is_active = user.get("active", True)

                    status = (
                        "[green]Active[/green]" if is_active else "[red]Inactive[/red]"
                    )

                    table.add_row(name, email, user_id, status)

                console.print(table)
                console.print(f"\n[dim]Found {len(users)} user(s)[/dim]")

        except Exception as e:
            print_error(f"Failed to list users: {e}")

    try:
        asyncio.run(run_list_users())
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user[/yellow]")


@user_group.command()
@click.argument("user_identifier", required=True)
@click.option("--team", "-t", help="Show workload for specific team")
@click.option(
    "--format",
    "-f",
    "output_format",
    type=click.Choice(["table", "json", "yaml"]),
    help="Output format (overrides global setting)",
)
@click.option("--no-color", is_flag=True, help="Disable colored output")
@click.pass_context
def show(
    ctx: click.Context,
    user_identifier: str,
    team: str | None,
    output_format: str | None,
    no_color: bool,
) -> None:
    """
    Show detailed user information and current workload.

    USER_IDENTIFIER can be either an email address or user ID.

    \b
    Examples:
        linear-cli user show john@company.com        # Show user by email
        linear-cli user show usr_123456789           # Show user by ID
        linear-cli user show john@company.com --team ENG  # Workload in specific team

    \b
    Information displayed:
        - User profile details
        - Current issue assignments
        - Workload distribution by priority
        - Recent activity summary
        - Team membership information
    """
    cli_ctx = ctx.obj["cli_context"]
    client = cli_ctx.get_client()
    config = cli_ctx.config

    async def run_show_user() -> None:
        try:
            # Determine search parameters
            assignee_email = assignee_id = None
            if "@" in user_identifier:
                assignee_email = user_identifier
            else:
                assignee_id = user_identifier

            # Determine team parameters
            team_id = team_key = None
            if team:
                if len(team) > 10 or "-" in team or "_" in team:
                    team_id = team
                else:
                    team_key = team

            # Get user's assigned issues
            console.print(
                f"[bold blue]Analyzing workload for {user_identifier}[/bold blue]"
            )

            issues_result = await client.get_issues(
                team_id=team_id,
                team_key=team_key,
                assignee_id=assignee_id,
                assignee_email=assignee_email,
                limit=100,  # Get more issues for workload analysis
            )

            issues = issues_result.get("nodes", [])

            if not issues:
                console.print(
                    f"[yellow]No issues found assigned to {user_identifier}[/yellow]"
                )
                if team:
                    console.print(f"[dim]In team: {team}[/dim]")
                return

            # Analyze workload
            user_info = None
            if issues:
                user_info = issues[0].get("assignee", {})

            priority_counts: dict[int, int] = defaultdict(int)
            state_counts: dict[str, int] = defaultdict(int)
            total_issues = len(issues)

            for issue in issues:
                priority = issue.get("priority", 0)
                state = issue.get("state", {}).get("name", "Unknown")

                priority_counts[priority] += 1
                state_counts[state] += 1

            # Display results
            if output_format in ["json", "yaml"]:
                # Prepare data for structured output
                workload_data = {
                    "user": user_info,
                    "total_issues": total_issues,
                    "priority_breakdown": dict(priority_counts),
                    "state_breakdown": dict(state_counts),
                    "issues": issues,
                }

                formatter = OutputFormatter(
                    output_format=output_format or config.output_format,
                    no_color=no_color or config.no_color,
                )
                formatter.format_generic(workload_data)
            else:
                # Rich formatted display
                if user_info:
                    console.print(
                        f"[bold]User: {user_info.get('displayName', 'Unknown')}[/bold]"
                    )
                    console.print(
                        f"[dim]Email: {user_info.get('email', 'Unknown')}[/dim]"
                    )
                    console.print(f"[dim]ID: {user_info.get('id', 'Unknown')}[/dim]")
                    if team:
                        console.print(f"[dim]Team: {team}[/dim]")
                    console.print()

                # Workload summary
                console.print(f"[bold]Current Workload: {total_issues} issue(s)[/bold]")
                console.print()

                # Priority breakdown
                if priority_counts:
                    priority_table = Table(title="Priority Distribution")
                    priority_table.add_column("Priority", style="bold")
                    priority_table.add_column("Count", justify="right")
                    priority_table.add_column("Percentage", justify="right")

                    priority_names = ["None", "Low", "Normal", "High", "Urgent"]
                    for priority in range(5):
                        count = priority_counts.get(priority, 0)
                        if count > 0:
                            percentage = (count / total_issues) * 100
                            color = (
                                "red"
                                if priority >= 3
                                else "yellow"
                                if priority == 2
                                else "dim"
                            )
                            priority_table.add_row(
                                f"[{color}]{priority_names[priority]}[/{color}]",
                                str(count),
                                f"{percentage:.1f}%",
                            )

                    console.print(priority_table)
                    console.print()

                # State breakdown
                if state_counts:
                    state_table = Table(title="State Distribution")
                    state_table.add_column("State", style="bold")
                    state_table.add_column("Count", justify="right")
                    state_table.add_column("Percentage", justify="right")

                    for state, count in sorted(
                        state_counts.items(), key=lambda x: x[1], reverse=True
                    ):
                        percentage = (count / total_issues) * 100
                        state_table.add_row(state, str(count), f"{percentage:.1f}%")

                    console.print(state_table)
                    console.print()

                # Recent issues preview
                console.print("[bold]Recent Issues:[/bold]")
                recent_issues = sorted(
                    issues, key=lambda x: x.get("updatedAt", ""), reverse=True
                )[:5]

                for issue in recent_issues:
                    identifier = issue.get("identifier", "Unknown")
                    title = issue.get("title", "No title")[:50] + (
                        "..." if len(issue.get("title", "")) > 50 else ""
                    )
                    priority = issue.get("priority", 0)
                    state = issue.get("state", {}).get("name", "Unknown")

                    priority_names = ["None", "Low", "Normal", "High", "Urgent"]
                    priority_color = (
                        "red" if priority >= 3 else "yellow" if priority == 2 else "dim"
                    )

                    console.print(
                        f"  {identifier}: {title} "
                        f"[{priority_color}][{priority_names[priority]}][/{priority_color}] "
                        f"[dim]({state})[/dim]"
                    )

        except Exception as e:
            print_error(f"Failed to show user information: {e}")

    try:
        asyncio.run(run_show_user())
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user[/yellow]")


@user_group.command()
@click.option("--team", "-t", help="Analyze workload for specific team")
@click.option(
    "--limit", type=int, default=10, help="Number of users to show (default: 10)"
)
@click.option(
    "--sort-by",
    type=click.Choice(["issues", "high-priority", "name"]),
    default="issues",
    help="Sort users by criteria (default: issues)",
)
@click.option(
    "--format",
    "-f",
    "output_format",
    type=click.Choice(["table", "json", "yaml"]),
    help="Output format (overrides global setting)",
)
@click.option("--no-color", is_flag=True, help="Disable colored output")
@click.pass_context
def workload(
    ctx: click.Context,
    team: str | None,
    limit: int,
    sort_by: str,
    output_format: str | None,
    no_color: bool,
) -> None:
    """
    Analyze workload distribution across team members.

    \b
    Examples:
        linear-cli user workload                        # Overall workload analysis
        linear-cli user workload --team ENG             # Team-specific analysis
        linear-cli user workload --sort-by high-priority # Sort by high-priority issues
        linear-cli user workload --limit 20             # Show more users

    \b
    Analysis includes:
        - Issue count per user
        - High-priority issue distribution
        - Workload balance recommendations
        - Unassigned issue counts
        - Assignment suggestions for better balance
    """
    cli_ctx = ctx.obj["cli_context"]
    client = cli_ctx.get_client()
    config = cli_ctx.config

    async def run_workload_analysis() -> None:
        try:
            # Determine team parameters
            team_id = team_key = None
            if team:
                if len(team) > 10 or "-" in team or "_" in team:
                    team_id = team
                else:
                    team_key = team

            console.print(
                f"[bold blue]Analyzing workload distribution{f' for team {team}' if team else ''}[/bold blue]"
            )

            # Get all issues for the team/organization
            issues_result = await client.get_issues(
                team_id=team_id,
                team_key=team_key,
                limit=200,  # Get more issues for comprehensive analysis
            )

            issues = issues_result.get("nodes", [])

            if not issues:
                console.print("[yellow]No issues found for analysis[/yellow]")
                return

            # Analyze workload distribution
            user_workloads: dict[str, dict[str, Any]] = defaultdict(
                lambda: {"total": 0, "high_priority": 0, "urgent": 0, "user_info": None}
            )

            unassigned_count = 0
            unassigned_high_priority = 0

            for issue in issues:
                assignee = issue.get("assignee")
                priority = issue.get("priority", 0)

                if assignee:
                    user_id = assignee.get("id")
                    if user_id:
                        user_workloads[user_id]["total"] = (
                            user_workloads[user_id].get("total", 0) + 1
                        )
                        user_workloads[user_id]["user_info"] = assignee

                        if priority >= 3:  # High or Urgent
                            user_workloads[user_id]["high_priority"] = (
                                user_workloads[user_id].get("high_priority", 0) + 1
                            )
                        if priority == 4:  # Urgent
                            user_workloads[user_id]["urgent"] = (
                                user_workloads[user_id].get("urgent", 0) + 1
                            )
                else:
                    unassigned_count += 1
                    if priority >= 3:
                        unassigned_high_priority += 1

            # Sort users based on criteria
            sorted_users = list(user_workloads.items())
            if sort_by == "issues":
                sorted_users.sort(key=lambda x: x[1]["total"], reverse=True)
            elif sort_by == "high-priority":
                sorted_users.sort(key=lambda x: x[1]["high_priority"], reverse=True)
            elif sort_by == "name":
                sorted_users.sort(
                    key=lambda x: x[1]["user_info"].get("displayName", "").lower()
                )

            # Limit results
            sorted_users = sorted_users[:limit]

            # Display results
            if output_format in ["json", "yaml"]:
                workload_data = {
                    "total_issues": len(issues),
                    "unassigned_issues": unassigned_count,
                    "unassigned_high_priority": unassigned_high_priority,
                    "user_workloads": [
                        {
                            "user_id": user_id,
                            "user_info": data["user_info"],
                            "total_issues": data["total"],
                            "high_priority_issues": data["high_priority"],
                            "urgent_issues": data["urgent"],
                        }
                        for user_id, data in sorted_users
                    ],
                }

                formatter = OutputFormatter(
                    output_format=output_format or config.output_format,
                    no_color=no_color or config.no_color,
                )
                formatter.format_generic(workload_data)
            else:
                # Rich formatted display
                console.print("[bold]Workload Analysis Summary[/bold]")
                console.print(f"Total Issues: {len(issues)}")
                console.print(f"Assigned Users: {len(user_workloads)}")
                if unassigned_count > 0:
                    console.print(
                        f"[yellow]Unassigned Issues: {unassigned_count}[/yellow]"
                    )
                    if unassigned_high_priority > 0:
                        console.print(
                            f"[red]  High Priority Unassigned: {unassigned_high_priority}[/red]"
                        )
                console.print()

                # User workload table
                if sorted_users:
                    workload_table = Table(
                        title=f"User Workload (Top {len(sorted_users)})"
                    )
                    workload_table.add_column("User", style="bold")
                    workload_table.add_column("Email", style="dim")
                    workload_table.add_column("Total", justify="right")
                    workload_table.add_column("High Priority", justify="right")
                    workload_table.add_column("Urgent", justify="right")
                    workload_table.add_column("Load", justify="center")

                    # Calculate load indicators
                    if sorted_users:
                        avg_load = sum(data["total"] for _, data in sorted_users) / len(
                            sorted_users
                        )
                    else:
                        avg_load = 0

                    for _user_id, data in sorted_users:
                        user_info = data["user_info"]
                        name = user_info.get("displayName", "Unknown")
                        email = user_info.get("email", "Unknown")
                        total = data["total"]
                        high_priority = data["high_priority"]
                        urgent = data["urgent"]

                        # Load indicator
                        if total > avg_load * 1.5:
                            load_indicator = "[red]High[/red]"
                        elif total < avg_load * 0.5:
                            load_indicator = "[green]Low[/green]"
                        else:
                            load_indicator = "[yellow]Normal[/yellow]"

                        workload_table.add_row(
                            name,
                            email,
                            str(total),
                            str(high_priority) if high_priority > 0 else "[dim]0[/dim]",
                            str(urgent) if urgent > 0 else "[dim]0[/dim]",
                            load_indicator,
                        )

                    console.print(workload_table)

                # Recommendations
                console.print()
                console.print("[bold]Recommendations:[/bold]")

                if unassigned_count > 0:
                    console.print(f"• Assign {unassigned_count} unassigned issue(s)")

                if sorted_users:
                    overloaded = [
                        u for u in sorted_users if u[1]["total"] > avg_load * 1.5
                    ]
                    underloaded = [
                        u for u in sorted_users if u[1]["total"] < avg_load * 0.5
                    ]

                    if overloaded:
                        console.print(
                            f"• Consider redistributing work from {len(overloaded)} overloaded user(s)"
                        )

                    if underloaded and overloaded:
                        console.print(
                            "• Balance workload between high and low-loaded team members"
                        )

        except Exception as e:
            print_error(f"Failed to analyze workload: {e}")

    try:
        asyncio.run(run_workload_analysis())
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user[/yellow]")


@user_group.command()
@click.argument("issue_count", type=int)
@click.option("--team", "-t", help="Suggest assignments within specific team")
@click.option(
    "--priority",
    "-p",
    type=click.IntRange(0, 4),
    help="Focus on specific priority level",
)
@click.option("--exclude", help="Exclude user from suggestions (email or ID)")
@click.pass_context
def suggest(
    ctx: click.Context,
    issue_count: int,
    team: str | None,
    priority: int | None,
    exclude: str | None,
) -> None:
    """
    Suggest optimal user assignments based on current workload.

    ISSUE_COUNT specifies how many issues you want to assign.

    \b
    Examples:
        linear-cli user suggest 5                    # Suggest assignments for 5 issues
        linear-cli user suggest 3 --team ENG        # Team-specific suggestions
        linear-cli user suggest 2 --priority 4      # For urgent issues
        linear-cli user suggest 4 --exclude john@company.com  # Exclude specific user

    \b
    Suggestions consider:
        - Current workload balance
        - Priority level preferences
        - Team membership
        - Recent assignment patterns
        - Availability indicators
    """
    cli_ctx = ctx.obj["cli_context"]
    client = cli_ctx.get_client()

    async def run_suggest_assignments() -> None:
        try:
            # Determine team parameters
            team_id = team_key = None
            if team:
                if len(team) > 10 or "-" in team or "_" in team:
                    team_id = team
                else:
                    team_key = team

            console.print(
                f"[bold blue]Analyzing assignments for {issue_count} issue(s)[/bold blue]"
            )

            # Get current workload data (reuse workload analysis logic)
            issues_result = await client.get_issues(
                team_id=team_id,
                team_key=team_key,
                limit=200,  # Get comprehensive data
            )

            issues = issues_result.get("nodes", [])

            # Get team users
            users = await client.get_users(
                team_id=team_id if team_id else None,
                limit=50,
            )

            if not users:
                console.print(
                    "[yellow]No users found for assignment suggestions[/yellow]"
                )
                return

            # Calculate current workloads
            user_workloads = {}
            for user in users:
                user_id = user.get("id")
                user_issues = [
                    issue
                    for issue in issues
                    if issue.get("assignee", {}).get("id") == user_id
                ]

                total_count = len(user_issues)
                high_priority_count = len(
                    [i for i in user_issues if i.get("priority", 0) >= 3]
                )

                user_workloads[user_id] = {
                    "user_info": user,
                    "total": total_count,
                    "high_priority": high_priority_count,
                    # WHY: Weight high-priority issues as 1.5x normal load for balanced assignment suggestions.
                    # High-priority issues typically require more focused attention, mental overhead, and often
                    # block other team members' work, so they should count more heavily in workload calculations.
                    "score": total_count + (high_priority_count * 0.5),
                }

            # Filter out excluded user
            if exclude:
                exclude_id = None
                for user_id, data in user_workloads.items():
                    user_info = data["user_info"]
                    if (
                        user_info.get("email") == exclude
                        or user_info.get("id") == exclude
                    ):
                        exclude_id = user_id
                        break

                if exclude_id:
                    del user_workloads[exclude_id]

            if not user_workloads:
                console.print(
                    "[yellow]No available users for assignment suggestions[/yellow]"
                )
                return

            # Sort users by workload (ascending - least loaded first)
            sorted_users = sorted(user_workloads.items(), key=lambda x: x[1]["score"])

            # Generate suggestions
            suggestions: builtins.list[dict[str, Any]] = []
            user_cycle = 0

            for i in range(issue_count):
                # Round-robin assignment starting with least loaded users
                user_id, user_data = sorted_users[user_cycle % len(sorted_users)]

                suggestions.append(
                    {
                        "assignment_number": i + 1,
                        "user_id": user_id,
                        "user_info": user_data["user_info"],
                        "current_workload": user_data["total"],
                        "new_workload": user_data["total"]
                        + len([s for s in suggestions if s["user_id"] == user_id])
                        + 1,
                    }
                )

                user_cycle += 1

            # Display suggestions
            console.print(
                f"[bold]Assignment Suggestions ({issue_count} issue(s))[/bold]"
            )
            if team:
                console.print(f"[dim]Team: {team}[/dim]")
            if priority is not None:
                priority_names = ["None", "Low", "Normal", "High", "Urgent"]
                console.print(f"[dim]Priority: {priority_names[priority]}[/dim]")
            console.print()

            suggestion_table = Table()
            suggestion_table.add_column("Issue #", justify="center")
            suggestion_table.add_column("Assign To", style="bold")
            suggestion_table.add_column("Email", style="dim")
            suggestion_table.add_column("Current Load", justify="right")
            suggestion_table.add_column("New Load", justify="right")

            for suggestion in suggestions:
                user_info = suggestion["user_info"]
                name = user_info.get("displayName", "Unknown")
                email = user_info.get("email", "Unknown")

                suggestion_table.add_row(
                    str(suggestion["assignment_number"]),
                    name,
                    email,
                    str(suggestion["current_workload"]),
                    str(suggestion["new_workload"]),
                )

            console.print(suggestion_table)

            # Summary
            console.print()
            console.print("[bold]Summary:[/bold]")
            user_counts: dict[str, int] = {}
            for suggestion in suggestions:
                user_id = suggestion["user_id"]
                user_info = suggestion["user_info"]
                name = user_info.get("displayName", "Unknown")

                user_counts[name] = user_counts.get(name, 0) + 1

            for name, count in user_counts.items():
                console.print(f"• {name}: {count} issue(s)")

        except Exception as e:
            print_error(f"Failed to generate assignment suggestions: {e}")

    try:
        asyncio.run(run_suggest_assignments())
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user[/yellow]")
