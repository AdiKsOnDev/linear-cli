"""
Search commands for Linearator CLI.

Provides full-text search capabilities across Linear issues with advanced filtering options.
"""

import asyncio
import logging

import click
from rich.console import Console

from ..formatters import OutputFormatter, print_error

logger = logging.getLogger(__name__)
console = Console()


@click.group()
def search_group() -> None:
    """Search Linear issues with advanced filters."""
    pass


@search_group.command(name="issues")
@click.argument("query", required=True)
@click.option("--team", "-t", help="Filter by team ID or key")
@click.option("--assignee", "-a", help="Filter by assignee email or ID")
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
    "--limit",
    type=click.IntRange(1, 100),
    default=25,
    help="Maximum number of results to return (default: 25)",
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
def search_issues(
    ctx: click.Context,
    query: str,
    team: str | None,
    assignee: str | None,
    state: str | None,
    labels: list[str] | None,
    priority: int | None,
    limit: int,
    output_format: str | None,
    no_color: bool,
) -> None:
    """
    Search Linear issues using full-text search with advanced filters.

    The QUERY argument supports Linear's full-text search syntax, which allows you to search
    across issue titles, descriptions, comments, and other text fields.

    \b
    Search Examples:
        linear-cli search issues "authentication bug"
        linear-cli search issues "API timeout" --team ENG --priority 3
        linear-cli search issues "login" --assignee john@example.com --state "In Progress"
        linear-cli search issues "database" --labels "bug,high-priority" --limit 10

    \b
    Advanced Search Syntax:
        - Simple terms: authentication bug
        - Quoted phrases: "API timeout error"
        - Exclude terms: authentication -login
        - Combine with filters for precise results

    \b
    Filter Options:
        --team: Filter by team key (e.g., ENG) or ID
        --assignee: Filter by user email or ID
        --state: Filter by workflow state name
        --labels: Filter by label names (comma-separated)
        --priority: Filter by priority level (0-4)
        --limit: Control number of results returned

    \b
    Output Formats:
        table: Rich formatted table with colors (default)
        json: Machine-readable JSON output
        yaml: Human-readable YAML output
    """
    cli_ctx = ctx.obj["cli_context"]
    client = cli_ctx.get_client()
    config = cli_ctx.config

    async def run_search() -> None:
        # Determine team parameters
        team_id = None
        team_key = None
        if team:
            # WHY: Linear uses different formats for IDs vs keys:
            # - Team IDs: long strings with dashes (e.g., "team_01H9XXXX-XXXX-XXXX")
            # - Team Keys: short alphanumeric codes (e.g., "ENG", "DESIGN")
            # This heuristic determines the parameter type based on length and character patterns
            # to enable users to use either format naturally without knowing the difference
            if len(team) > 10 or "-" in team or "_" in team:
                team_id = team
            else:
                team_key = team

        # Determine assignee parameters
        assignee_id = None
        assignee_email = None
        if assignee:
            if "@" in assignee:
                assignee_email = assignee
            else:
                assignee_id = assignee

        # Execute search
        results = await client.search_issues(
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

        # Format and display results
        formatter = OutputFormatter(
            output_format=output_format or config.output_format,
            no_color=no_color or config.no_color,
        )

        issues = results.get("nodes", [])
        page_info = results.get("pageInfo", {})

        if not issues:
            console.print(f"[yellow]No issues found matching '{query}'[/yellow]")
            if any([team, assignee, state, labels, priority]):
                console.print("[dim]Try adjusting your filters or search terms[/dim]")
            return

        # Display search header
        filter_info = []
        if team:
            filter_info.append(f"team:{team}")
        if assignee:
            filter_info.append(f"assignee:{assignee}")
        if state:
            filter_info.append(f"state:{state}")
        if labels:
            filter_info.append(f"labels:{','.join(labels)}")
        if priority is not None:
            priority_names = ["None", "Low", "Normal", "High", "Urgent"]
            filter_info.append(f"priority:{priority_names[priority]}")

        search_desc = f"Search: '{query}'"
        if filter_info:
            search_desc += f" ({', '.join(filter_info)})"

        console.print(f"[bold blue]{search_desc}[/bold blue]")
        console.print(f"[dim]Found {len(issues)} issue(s)[/dim]")
        console.print()

        # Format and display issues
        formatter.format_issues(issues)

        # Show pagination info if available
        if page_info.get("hasNextPage"):
            console.print()
            console.print(
                "[dim]More results available. Use pagination options to see additional results.[/dim]"
            )

    try:
        asyncio.run(run_search())
    except Exception as e:
        print_error(f"Search failed: {e}")


@search_group.command(name="history")
@click.pass_context
def search_history(ctx: click.Context) -> None:
    """Show search history (placeholder for future implementation)."""
    console.print(
        "[yellow]Search history feature will be implemented in a future version.[/yellow]"
    )
    console.print("This will show your recent searches and allow you to re-run them.")


@search_group.command(name="save")
@click.argument("name")
@click.argument("query")
@click.option("--description", help="Description of the saved search")
@click.pass_context
def save_search(
    ctx: click.Context, name: str, query: str, description: str | None
) -> None:
    """Save a search query for later use (placeholder for future implementation)."""
    console.print(
        "[yellow]Saved searches feature will be implemented in a future version.[/yellow]"
    )
    console.print(f"Would save search '{name}' with query: {query}")
    if description:
        console.print(f"Description: {description}")


@search_group.command(name="list")
@click.pass_context
def list_saved_searches(ctx: click.Context) -> None:
    """List saved searches (placeholder for future implementation)."""
    console.print(
        "[yellow]Saved searches feature will be implemented in a future version.[/yellow]"
    )
    console.print("This will show your saved search queries.")


# Alias the main search command for convenience
@click.command()
@click.argument("query", required=True)
@click.option("--team", "-t", help="Filter by team ID or key")
@click.option("--assignee", "-a", help="Filter by assignee email or ID")
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
    "--limit",
    type=click.IntRange(1, 100),
    default=25,
    help="Maximum number of results to return (default: 25)",
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
def search(
    ctx: click.Context,
    query: str,
    team: str | None,
    assignee: str | None,
    state: str | None,
    labels: list[str] | None,
    priority: int | None,
    limit: int,
    output_format: str | None,
    no_color: bool,
) -> None:
    """
    Search Linear issues (alias for 'search issues').

    This is a convenient alias for the main search functionality.
    See 'linear-cli search issues --help' for detailed usage information.
    """
    # Forward to the main search_issues command
    ctx.invoke(
        search_issues,
        query=query,
        team=team,
        assignee=assignee,
        state=state,
        labels=labels,
        priority=priority,
        limit=limit,
        output_format=output_format,
        no_color=no_color,
    )
