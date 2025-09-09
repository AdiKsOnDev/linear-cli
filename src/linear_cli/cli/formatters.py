"""
Output formatters for CLI commands.

Provides various output formats including tables, JSON, and colored text.
"""

import json
from datetime import datetime
from typing import Any

from rich.console import Console
from rich.json import JSON
from rich.markdown import Markdown
from rich.table import Table
from rich.text import Text

from ..constants import (
    DEFAULT_COLOR_STYLE,
    DEFAULT_PRIORITY,
    DEFAULT_STATE_COLOR,
    PRIORITY_LEVELS,
)
from ..utils.helpers import format_datetime as format_datetime_util

console = Console()


def format_datetime(dt_str: str | None) -> str:
    """Format datetime string for display."""
    if not dt_str:
        return ""

    try:
        dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        # Convert to UTC for consistent display
        utc_dt = dt.utctimetuple()
        utc_datetime = datetime(*utc_dt[:6])
        return utc_datetime.strftime("%Y-%m-%d %H:%M")
    except (ValueError, AttributeError):
        return dt_str or ""


def get_priority_text(priority: int | None) -> Text:
    """Get formatted priority text with color."""
    if priority is None or priority not in PRIORITY_LEVELS:
        priority = DEFAULT_PRIORITY

    text, style = PRIORITY_LEVELS[priority]
    return Text(text, style=style)


def get_state_text(state: dict[str, Any] | None) -> Text:
    """Get formatted state text with color."""
    if not state:
        return Text("Unknown", style="dim")

    name = state.get("name") or "Unknown"
    color = state.get("color", DEFAULT_STATE_COLOR)

    # WHY: Linear provides hex colors (like "#ff0000") but terminal Rich library uses named colors
    # We need to approximate hex colors to the nearest terminal color for consistent display
    # This heuristic works well for common Linear state colors (red=blocked, green=done, etc.)
    style = DEFAULT_COLOR_STYLE
    if color:
        # Simple color mapping based on common Linear state colors
        color_lower = color.lower()
        if "ff" in color_lower[:3]:  # Red-ish (blocked, urgent states)
            style = "red"
        elif (
            "00ff" in color_lower or "0f0" in color_lower
        ):  # Green-ish (done, completed states)
            style = "green"
        elif (
            "ff0" in color_lower or "ffff00" in color_lower
        ):  # Yellow-ish (in progress, warning states)
            style = "yellow"
        elif (
            "00" in color_lower and "ff" in color_lower
        ):  # Blue-ish (todo, planning states)
            style = "blue"

    return Text(name, style=style)


def format_labels(labels: dict[str, Any] | list | None) -> str:
    """Format labels list for display."""
    if not labels:
        return ""

    # Handle GraphQL format {"nodes": [...]}
    if isinstance(labels, dict):
        if not labels.get("nodes"):
            return ""
        label_list = labels["nodes"]
    # Handle plain list format
    elif isinstance(labels, list):
        label_list = labels
    else:
        return ""

    label_names = [label.get("name", "") for label in label_list if label]
    return ", ".join(label_names)


def truncate_text(text: str | None, max_length: int = 50) -> str:
    """Truncate text to max length with ellipsis."""
    if not text:
        return ""

    if len(text) <= max_length:
        return text

    return text[: max_length - 3] + "..."


class OutputFormatter:
    """Base class for output formatters."""

    def __init__(self, output_format: str = "table", no_color: bool = False):
        """
        Initialize formatter.

        Args:
            output_format: Output format ('table', 'json', 'yaml')
            no_color: Whether to disable colored output
        """
        self.output_format = output_format
        self.no_color = no_color

    def format_issues(self, issues_data: dict[str, Any]) -> None:
        """Format and display issues data."""
        issues = issues_data.get("nodes", [])

        if self.output_format == "json":
            self._print_json(issues)
        else:
            self._format_issues_table(issues)

    def format_issue(self, issue: dict[str, Any]) -> None:
        """Format and display single issue data."""
        if self.output_format == "json":
            self._print_json(issue)
        else:
            self._format_issue_details(issue)

    def format_teams(self, teams: list[dict[str, Any]]) -> None:
        """Format and display teams data."""
        if self.output_format == "json":
            self._print_json(teams)
        else:
            self._format_teams_table(teams)

    def format_labels(self, labels_data: dict[str, Any]) -> None:
        """Format and display labels data."""
        labels = labels_data.get("nodes", [])

        if self.output_format == "json":
            self._print_json(labels)
        else:
            self._format_labels_table(labels)

    def format_users(self, users: list[dict[str, Any]]) -> None:
        """Format and display users data."""
        if self.output_format == "json":
            self._print_json(users)
        else:
            self._format_users_table(users)

    def _print_json(self, data: Any) -> None:
        """Print data as JSON."""
        if self.no_color:
            console.print(json.dumps(data, indent=2))
        else:
            console.print(JSON.from_data(data))

    def _format_issues_table(self, issues: list[dict[str, Any]]) -> None:
        """Format issues as a table."""
        if not issues:
            console.print("[yellow]No issues found.[/yellow]")
            return

        table = Table(show_header=True, header_style="bold blue")
        table.add_column("ID", style="cyan", width=12)
        table.add_column("Title", style="bold")
        table.add_column("State", justify="center")
        table.add_column("Priority", justify="center")
        table.add_column("Assignee", style="dim")
        table.add_column("Team", style="green", width=8)
        table.add_column("Labels", style="magenta")
        table.add_column("Updated", style="dim", width=12)

        for issue in issues:
            # Get assignee name
            assignee = issue.get("assignee")
            assignee_name = ""
            if assignee:
                assignee_name = assignee.get("displayName") or assignee.get("name", "")

            # Get team key
            team = issue.get("team")
            team_key = team.get("key", "") if team else ""

            # Format labels
            labels_str = format_labels(issue.get("labels"))

            table.add_row(
                issue.get("identifier", ""),
                truncate_text(issue.get("title", ""), 40),
                get_state_text(issue.get("state")),
                get_priority_text(issue.get("priority")),
                truncate_text(assignee_name, 15),
                team_key,
                truncate_text(labels_str, 20),
                format_datetime(issue.get("updatedAt")),
            )

        console.print(table)
        console.print(f"\n[dim]Found {len(issues)} issue(s)[/dim]")

    def _format_issue_details(self, issue: dict[str, Any]) -> None:
        """Format detailed issue information."""
        console.print(
            f"[bold cyan]{issue.get('identifier', '')}[/bold cyan]: {issue.get('title', '')}"
        )
        console.print()

        # Basic info
        console.print("[dim]URL:[/dim]", issue.get("url", ""))

        state = issue.get("state")
        if state:
            console.print("[dim]State:[/dim]", get_state_text(state))

        priority = issue.get("priority")
        if priority is not None:
            console.print("[dim]Priority:[/dim]", get_priority_text(priority))

        # People
        assignee = issue.get("assignee")
        if assignee:
            assignee_name = assignee.get("displayName") or assignee.get("name", "")
            console.print(f"[dim]Assignee:[/dim] {assignee_name}")

        creator = issue.get("creator")
        if creator:
            creator_name = creator.get("displayName") or creator.get("name", "")
            console.print(f"[dim]Creator:[/dim] {creator_name}")

        # Team
        team = issue.get("team")
        if team:
            console.print(
                f"[dim]Team:[/dim] {team.get('name', '')} ({team.get('key', '')})"
            )

        # Project
        project = issue.get("project")
        if project:
            console.print(f"[dim]Project:[/dim] {project.get('name', '')}")

        # Labels
        labels_str = format_labels(issue.get("labels"))
        if labels_str:
            console.print(f"[dim]Labels:[/dim] {labels_str}")

        # Dates
        console.print(f"[dim]Created:[/dim] {format_datetime(issue.get('createdAt'))}")
        console.print(f"[dim]Updated:[/dim] {format_datetime(issue.get('updatedAt'))}")

        if issue.get("completedAt"):
            console.print(
                f"[dim]Completed:[/dim] {format_datetime(issue.get('completedAt'))}"
            )

        # Description
        description = issue.get("description")
        if description:
            console.print()
            console.print("[dim]Description:[/dim]")
            # Render markdown in terminal using Rich's Markdown
            try:
                markdown = Markdown(description)
                console.print(markdown)
            except Exception:
                # Fallback to plain text if markdown rendering fails
                console.print(description)

        # Comments
        comments = issue.get("comments", {}).get("nodes", [])
        if comments:
            console.print()
            console.print(f"[dim]Comments ({len(comments)}):[/dim]")
            for comment in comments[:3]:  # Show first 3 comments
                user = comment.get("user", {})
                user_name = user.get("displayName") or user.get("name", "Unknown")
                created = format_datetime(comment.get("createdAt"))
                body = truncate_text(comment.get("body", ""), 100)
                console.print(
                    f"  [cyan]{user_name}[/cyan] [dim]({created}):[/dim] {body}"
                )

            if len(comments) > 3:
                console.print(f"  [dim]... and {len(comments) - 3} more comments[/dim]")

    def _format_teams_table(self, teams: list[dict[str, Any]]) -> None:
        """Format teams as a table."""
        if not teams:
            console.print("[yellow]No teams found.[/yellow]")
            return

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
                str(len(team.get("members", {}).get("nodes", []))),
                team_type,
            )

        console.print(table)
        console.print(f"\n[dim]Found {len(teams)} team(s)[/dim]")

    def _format_labels_table(self, labels: list[dict[str, Any]]) -> None:
        """Format labels as a table."""
        if not labels:
            console.print("[yellow]No labels found.[/yellow]")
            return

        table = Table(show_header=True, header_style="bold blue")
        table.add_column("Name", style="bold")
        table.add_column("Color", justify="center")
        table.add_column("Description", style="dim")
        table.add_column("Team", style="green")
        table.add_column("Created", style="dim", width=12)

        # Sort labels by name
        labels_sorted = sorted(labels, key=lambda x: x.get("name", ""))

        for label in labels_sorted:
            team = label.get("team")
            team_name = team.get("key", "") if team else "Global"

            # Show color as colored text
            color = label.get("color", "#808080")
            color_display = Text("●", style=f"color({color})")

            table.add_row(
                label.get("name", ""),
                color_display,
                truncate_text(label.get("description", ""), 40),
                team_name,
                format_datetime(label.get("createdAt")),
            )

        console.print(table)
        console.print(f"\n[dim]Found {len(labels)} label(s)[/dim]")

    def _format_users_table(self, users: list[dict[str, Any]]) -> None:
        """Format users as a table."""
        if not users:
            console.print("[yellow]No users found.[/yellow]")
            return

        table = Table(show_header=True, header_style="bold blue")
        table.add_column("Name", style="bold")
        table.add_column("Display Name", style="cyan")
        table.add_column("Email", style="dim")
        table.add_column("Status", justify="center")
        table.add_column("Role", justify="center")

        # Sort users by name
        users_sorted = sorted(users, key=lambda x: x.get("name", ""))

        for user in users_sorted:
            status = "Active" if user.get("active", False) else "Inactive"
            status_style = "green" if user.get("active", False) else "red"

            role = "Admin" if user.get("admin", False) else "Member"
            role_style = "yellow" if user.get("admin", False) else "dim"

            table.add_row(
                user.get("name", ""),
                user.get("displayName", ""),
                user.get("email", ""),
                Text(status, style=status_style),
                Text(role, style=role_style),
            )

        console.print(table)
        console.print(f"\n[dim]Found {len(users)} user(s)[/dim]")

    def format_generic(self, data: Any) -> None:
        """Format generic data structure."""
        if self.output_format == "json":
            self._print_json(data)
        else:
            # For table format, just print as JSON since we don't know the structure
            console.print(
                "[yellow]Generic data (use --format json for better output):[/yellow]"
            )
            self._print_json(data)


def print_success(message: str) -> None:
    """Print success message."""
    console.print(f"[green]✓ {message}[/green]")


def print_error(message: str) -> None:
    """Print error message."""
    console.print(f"[red]✗ {message}[/red]")


def print_warning(message: str) -> None:
    """Print warning message."""
    console.print(f"[yellow]⚠ {message}[/yellow]")


def print_info(message: str) -> None:
    """Print info message."""
    console.print(f"[blue]ℹ {message}[/blue]")


# Add project formatting methods to OutputFormatter class
def _add_project_methods():
    """Add project formatting methods to OutputFormatter class."""

    def format_projects(self, projects_data: dict[str, Any]) -> None:
        """Format projects data for output."""
        if self.output_format == "json":
            console.print(JSON(json.dumps(projects_data, default=str, indent=2)))
        else:
            projects = projects_data.get("nodes", [])
            self._format_projects_table(projects)

    def format_project(self, project: dict[str, Any]) -> None:
        """Format project details for output."""
        if self.output_format == "json":
            console.print(JSON(json.dumps(project, default=str, indent=2)))
        else:
            self._format_project_details(project)

    def format_project_updates(self, updates_data: dict[str, Any]) -> None:
        """Format project updates data for output."""
        if self.output_format == "json":
            console.print(JSON(json.dumps(updates_data, default=str, indent=2)))
        else:
            updates = updates_data.get("nodes", [])
            self._format_project_updates_table(updates)

    def _format_projects_table(self, projects: list[dict[str, Any]]) -> None:
        """Format projects as a table."""
        if not projects:
            console.print("[dim]No projects found.[/dim]")
            return

        table = Table(title="Projects", show_header=True, header_style="bold magenta")

        table.add_column("Name", style="cyan", min_width=20)
        table.add_column("State", style="yellow", min_width=10)
        table.add_column("Health", style="green", min_width=10)
        table.add_column("Progress", style="blue", min_width=8)
        table.add_column("Lead", min_width=15)
        table.add_column("Target", min_width=12)
        table.add_column("Description", min_width=30)

        for project in projects:
            name = project.get("name", "")
            state = project.get("state", "")
            health = project.get("health", "")
            progress = f"{project.get('progress', 0):.0f}%" if project.get("progress") else ""

            lead = project.get("lead")
            lead_name = ""
            if lead:
                lead_name = lead.get("displayName") or lead.get("name", "")

            target_date = format_datetime_util(project.get("targetDate"), "short") if project.get("targetDate") else "No target"
            description = truncate_text(project.get("description", ""), 50)

            table.add_row(
                name,
                state,
                health,
                progress,
                lead_name,
                target_date,
                description,
            )

        console.print(table)

    def _format_project_details(self, project: dict[str, Any]) -> None:
        """Format detailed project information."""
        console.print(f"[bold cyan]{project.get('name', '')}[/bold cyan]")
        console.print()

        # Basic info
        console.print("[dim]URL:[/dim]", project.get("url", ""))

        state = project.get("state")
        if state:
            console.print(f"[dim]State:[/dim] {state}")

        health = project.get("health")
        if health:
            console.print(f"[dim]Health:[/dim] {health}")

        progress = project.get("progress")
        if progress is not None:
            console.print(f"[dim]Progress:[/dim] {progress:.0f}%")

        # People
        lead = project.get("lead")
        if lead:
            lead_name = lead.get("displayName") or lead.get("name", "")
            console.print(f"[dim]Lead:[/dim] {lead_name}")

        creator = project.get("creator")
        if creator:
            creator_name = creator.get("displayName") or creator.get("name", "")
            console.print(f"[dim]Creator:[/dim] {creator_name}")

        # Teams
        teams = project.get("teams", {}).get("nodes", [])
        if teams:
            team_names = [f"{team.get('name', '')} ({team.get('key', '')})" for team in teams]
            console.print(f"[dim]Teams:[/dim] {', '.join(team_names)}")

        # Dates
        start_date = format_datetime_util(project.get("startDate"), "short") if project.get("startDate") else None
        if start_date:
            console.print(f"[dim]Start Date:[/dim] {start_date}")

        target_date = format_datetime_util(project.get("targetDate"), "short") if project.get("targetDate") else None
        if target_date:
            console.print(f"[dim]Target Date:[/dim] {target_date}")

        console.print(f"[dim]Created:[/dim] {format_datetime(project.get('createdAt'))}")
        console.print(f"[dim]Updated:[/dim] {format_datetime(project.get('updatedAt'))}")

        # Description
        description = project.get("description")
        if description:
            console.print()
            console.print("[dim]Description:[/dim]")
            try:
                markdown = Markdown(description)
                console.print(markdown)
            except Exception:
                console.print(description)

        # Recent updates
        updates = project.get("updates", {}).get("nodes", [])
        if updates:
            console.print()
            console.print("[dim]Recent Updates:[/dim]")
            for update in updates[:3]:  # Show only latest 3 updates
                user = update.get("user", {})
                user_name = user.get("displayName") or user.get("name", "")
                created_at = format_datetime(update.get("createdAt"))
                health = update.get("health", "")
                health_str = f" ({health})" if health else ""

                console.print(f"  [dim]{created_at} - {user_name}{health_str}:[/dim]")
                body = update.get("body", "")
                if body:
                    console.print(f"  {body}")
                console.print()

    def _format_project_updates_table(self, updates: list[dict[str, Any]]) -> None:
        """Format project updates as a table."""
        if not updates:
            console.print("[dim]No project updates found.[/dim]")
            return

        table = Table(title="Project Updates", show_header=True, header_style="bold magenta")

        table.add_column("Date", style="cyan", min_width=12)
        table.add_column("User", style="yellow", min_width=15)
        table.add_column("Health", style="green", min_width=10)
        table.add_column("Update", min_width=50)

        for update in updates:
            created_at = format_datetime(update.get("createdAt"))

            user = update.get("user", {})
            user_name = user.get("displayName") or user.get("name", "")

            health = update.get("health", "")
            body = truncate_text(update.get("body", ""), 80)

            table.add_row(
                created_at,
                user_name,
                health,
                body,
            )

        console.print(table)

    # Add methods to OutputFormatter class
    OutputFormatter.format_projects = format_projects
    OutputFormatter.format_project = format_project
    OutputFormatter.format_project_updates = format_project_updates
    OutputFormatter._format_projects_table = _format_projects_table
    OutputFormatter._format_project_details = _format_project_details
    OutputFormatter._format_project_updates_table = _format_project_updates_table

# Add the methods when module is imported
_add_project_methods()
