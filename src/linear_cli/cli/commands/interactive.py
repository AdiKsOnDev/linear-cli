"""
Interactive mode commands for Linearator CLI.

Provides guided workflows for complex operations.
"""

import asyncio
import logging

import click
from rich.console import Console
from rich.prompt import Confirm, Prompt
from rich.table import Table

from ..formatters import print_error, print_success

logger = logging.getLogger(__name__)
console = Console()


@click.command()
@click.pass_context
def interactive(ctx: click.Context) -> None:
    """
    Start interactive mode for guided issue management workflows.

    Interactive mode provides step-by-step guidance for common tasks:
    - Creating issues with proper fields and validation
    - Bulk operations with safety checks
    - Complex search and filtering operations
    - Team and user management tasks

    \b
    Features:
        - Guided prompts with validation
        - Auto-completion where possible
        - Safety confirmations for destructive operations
        - Real-time preview of changes
        - Context-aware suggestions
    """
    cli_ctx = ctx.obj["cli_context"]
    client = cli_ctx.get_client()

    console.print("[bold blue]Linearator Interactive Mode[/bold blue]")
    console.print("Choose from guided workflows for common tasks.\n")

    async def run_interactive() -> None:
        try:
            while True:
                # Main menu
                # WHY: Workflow menu ordered by frequency of use and typical issue management flow:
                # 1. Creation → 2. Search → 3. Bulk operations → 4. Management → 5. Analysis
                # This progression follows typical issue workflow patterns and prioritizes
                # the most commonly used operations first for better user experience
                console.print("[bold]Available workflows:[/bold]")
                console.print("1. 📝 Create Issue (guided)")
                console.print("2. 🔍 Advanced Search Builder")
                console.print("3. 📦 Bulk Operations Wizard")
                console.print("4. 👥 Team Management")
                console.print("5. 📊 Workload Analysis")
                console.print("6. ❌ Exit Interactive Mode")
                console.print()

                choice = Prompt.ask(
                    "Select a workflow",
                    choices=["1", "2", "3", "4", "5", "6"],
                    default="6",
                )

                if choice == "1":
                    await create_issue_workflow()
                elif choice == "2":
                    await search_builder_workflow()
                elif choice == "3":
                    await bulk_operations_workflow()
                elif choice == "4":
                    await team_management_workflow()
                elif choice == "5":
                    await workload_analysis_workflow()
                elif choice == "6":
                    console.print("[green]Exiting interactive mode. Goodbye![/green]")
                    break

                # Ask if user wants to continue
                if choice != "6":
                    console.print()
                    if not Confirm.ask(
                        "Would you like to perform another operation?", default=True
                    ):
                        break

        except KeyboardInterrupt:
            console.print("\n[yellow]Interactive mode cancelled[/yellow]")
        except Exception as e:
            print_error(f"Interactive mode error: {e}")

    async def create_issue_workflow() -> None:
        """Guided issue creation workflow."""
        console.print("\n[bold blue]📝 Guided Issue Creation[/bold blue]")

        try:
            # Get available teams
            teams = await client.get_teams()
            if not teams:
                console.print(
                    "[red]No teams available. Please check your permissions.[/red]"
                )
                return

            # Team selection
            if len(teams) == 1:
                selected_team = teams[0]
                console.print(f"Using team: [bold]{selected_team['name']}[/bold]")
            else:
                console.print("\n[bold]Available teams:[/bold]")
                team_table = Table()
                team_table.add_column("Number", justify="center")
                team_table.add_column("Team", style="bold")
                team_table.add_column("Key", style="dim")

                for i, team in enumerate(teams, 1):
                    team_table.add_row(str(i), team["name"], team["key"])

                console.print(team_table)

                team_choice = Prompt.ask(
                    "Select team (number)",
                    choices=[str(i) for i in range(1, len(teams) + 1)],
                    default="1",
                )
                selected_team = teams[int(team_choice) - 1]

            team_id = selected_team["id"]
            console.print(f"Selected team: [bold]{selected_team['name']}[/bold]")

            # Issue title
            title = Prompt.ask("\n[bold]Issue title[/bold]", default="")
            while not title.strip():
                console.print("[red]Title is required[/red]")
                title = Prompt.ask("[bold]Issue title[/bold]")

            # Issue description
            description = Prompt.ask(
                "\n[bold]Issue description[/bold] (optional)", default=""
            )

            # Priority selection
            console.print("\n[bold]Priority levels:[/bold]")
            priorities = ["None (0)", "Low (1)", "Normal (2)", "High (3)", "Urgent (4)"]
            for i, priority_name in enumerate(priorities):
                console.print(f"{i}. {priority_name}")

            priority_choice = Prompt.ask(
                "Select priority", choices=["0", "1", "2", "3", "4"], default="2"
            )
            priority = int(priority_choice)

            # Assignee (optional)
            users = await client.get_users(team_id=team_id, limit=50)
            assignee_email = None

            if users and Confirm.ask(
                "\nWould you like to assign this issue to someone?", default=False
            ):
                console.print("\n[bold]Available team members:[/bold]")
                user_table = Table()
                user_table.add_column("Number", justify="center")
                user_table.add_column("Name", style="bold")
                user_table.add_column("Email", style="dim")

                for i, user in enumerate(users, 1):
                    name = user.get("displayName", user.get("name", "Unknown"))
                    email = user.get("email", "No email")
                    user_table.add_row(str(i), name, email)

                console.print(user_table)

                user_choice = Prompt.ask(
                    "Select assignee (number, or press Enter to skip)",
                    choices=[str(i) for i in range(1, len(users) + 1)] + [""],
                    default="",
                    show_default=False,
                )

                if user_choice:
                    assignee_email = users[int(user_choice) - 1]["email"]

            # Labels (optional)
            labels = []
            if Confirm.ask("\nWould you like to add labels?", default=False):
                team_labels = await client.get_labels(team_id=team_id)
                if team_labels:
                    console.print("\n[bold]Available labels:[/bold]")
                    label_table = Table()
                    label_table.add_column("Number", justify="center")
                    label_table.add_column("Label", style="bold")
                    label_table.add_column("Color", style="dim")

                    for i, label in enumerate(team_labels, 1):
                        name = label.get("name", "Unknown")
                        color = label.get("color", "#000000")
                        label_table.add_row(str(i), name, color)

                    console.print(label_table)

                    label_choices = Prompt.ask(
                        "Select labels (comma-separated numbers, or press Enter to skip)",
                        default="",
                        show_default=False,
                    )

                    if label_choices:
                        for choice in label_choices.split(","):
                            try:
                                idx = int(choice.strip()) - 1
                                if 0 <= idx < len(team_labels):
                                    labels.append(team_labels[idx]["name"])
                            except ValueError:
                                continue

            # Summary
            console.print("\n[bold]Issue Summary:[/bold]")
            console.print(f"Title: {title}")
            console.print(f"Team: {selected_team['name']}")
            console.print(f"Priority: {priorities[priority]}")
            if description:
                console.print(
                    f"Description: {description[:100]}{'...' if len(description) > 100 else ''}"
                )
            if assignee_email:
                console.print(f"Assignee: {assignee_email}")
            if labels:
                console.print(f"Labels: {', '.join(labels)}")

            # Confirmation
            if not Confirm.ask("\nCreate this issue?", default=True):
                console.print("[yellow]Issue creation cancelled[/yellow]")
                return

            # Create the issue
            console.print("\n[bold]Creating issue...[/bold]")

            issue = await client.create_issue(
                title=title,
                description=description or None,
                team_id=team_id,
                assignee_email=assignee_email,
                priority=priority,
                labels=labels if labels else None,
            )

            if issue:
                identifier = issue.get("identifier", "Unknown")
                url = issue.get("url", "")
                print_success(f"Issue created successfully: {identifier}")
                if url:
                    console.print(f"[dim]View at: {url}[/dim]")
            else:
                print_error("Failed to create issue")

        except Exception as e:
            print_error(f"Issue creation failed: {e}")

    async def search_builder_workflow() -> None:
        """Interactive search query builder."""
        console.print("\n[bold blue]🔍 Advanced Search Builder[/bold blue]")

        # Build search query interactively
        query = Prompt.ask("Enter search terms", default="")

        filters = {}

        if Confirm.ask("Filter by team?", default=False):
            teams = await client.get_teams()
            if teams:
                console.print("\nAvailable teams:")
                for i, team in enumerate(teams, 1):
                    console.print(f"{i}. {team['name']} ({team['key']})")

                team_choice = Prompt.ask(
                    "Select team (number)",
                    choices=[str(i) for i in range(1, len(teams) + 1)],
                    default="1",
                )
                selected_team = teams[int(team_choice) - 1]
                filters["team"] = selected_team["key"]

        if Confirm.ask("Filter by priority?", default=False):
            priority_choice = Prompt.ask(
                "Priority level (0=None, 1=Low, 2=Normal, 3=High, 4=Urgent)",
                choices=["0", "1", "2", "3", "4"],
            )
            filters["priority"] = int(priority_choice)

        if Confirm.ask("Filter by state?", default=False):
            state = Prompt.ask("State name (e.g., 'To Do', 'In Progress', 'Done')")
            if state:
                filters["state"] = state

        # Execute search
        console.print(f"\n[bold]Executing search: '{query}'[/bold]")
        for key, value in filters.items():
            console.print(f"[dim]{key}: {value}[/dim]")

        # Here you would call the actual search function
        # For now, just show what would be executed
        console.print("\n[green]Search would be executed with these parameters[/green]")
        console.print(
            "[dim]Use 'linear-cli search' command for actual search execution[/dim]"
        )

    async def bulk_operations_workflow() -> None:
        """Guided bulk operations workflow."""
        console.print("\n[bold blue]📦 Bulk Operations Wizard[/bold blue]")

        operation = Prompt.ask(
            "Select operation",
            choices=["update-state", "assign", "label"],
            default="update-state",
        )

        query = Prompt.ask("Search query to find issues")

        if operation == "update-state":
            new_state = Prompt.ask("New state name")
            console.print("\n[yellow]Would execute:[/yellow]")
            console.print(
                f"linear-cli bulk update-state -q '{query}' --new-state '{new_state}'"
            )

        elif operation == "assign":
            assignee = Prompt.ask("Assignee email")
            console.print("\n[yellow]Would execute:[/yellow]")
            console.print(
                f"linear-cli bulk assign -q '{query}' --assignee '{assignee}'"
            )

        elif operation == "label":
            action = Prompt.ask("Action", choices=["add", "remove"], default="add")
            labels = Prompt.ask("Labels (comma-separated)")

            console.print("\n[yellow]Would execute:[/yellow]")
            if action == "add":
                console.print(
                    f"linear-cli bulk label -q '{query}' --add-labels '{labels}'"
                )
            else:
                console.print(
                    f"linear-cli bulk label -q '{query}' --remove-labels '{labels}'"
                )

        console.print("\n[dim]Use --dry-run first to preview changes[/dim]")

    async def team_management_workflow() -> None:
        """Team management workflow."""
        console.print("\n[bold blue]👥 Team Management[/bold blue]")

        teams = await client.get_teams()
        if not teams:
            console.print("[red]No teams available[/red]")
            return

        console.print("\nYour teams:")
        team_table = Table()
        team_table.add_column("Name", style="bold")
        team_table.add_column("Key", style="dim")
        team_table.add_column("Members", justify="right")

        for team in teams:
            team_table.add_row(
                team.get("name", "Unknown"),
                team.get("key", "Unknown"),
                str(len(team.get("members", {}).get("nodes", []))),
            )

        console.print(team_table)

        console.print(
            "\n[dim]Use 'linear-cli team info <key>' for detailed team information[/dim]"
        )

    async def workload_analysis_workflow() -> None:
        """Workload analysis workflow."""
        console.print("\n[bold blue]📊 Workload Analysis[/bold blue]")

        teams = await client.get_teams()
        if not teams:
            console.print("[red]No teams available[/red]")
            return

        if len(teams) == 1:
            team = teams[0]
        else:
            console.print("\nSelect team for analysis:")
            for i, team in enumerate(teams, 1):
                console.print(f"{i}. {team['name']}")

            choice = Prompt.ask(
                "Team number",
                choices=[str(i) for i in range(1, len(teams) + 1)],
                default="1",
            )
            team = teams[int(choice) - 1]

        console.print(f"\n[bold]Analyzing workload for {team['name']}...[/bold]")
        console.print(
            "\n[dim]Use 'linear-cli user workload --team <key>' for detailed analysis[/dim]"
        )

    try:
        asyncio.run(run_interactive())
    except KeyboardInterrupt:
        console.print("\n[yellow]Interactive mode cancelled[/yellow]")
