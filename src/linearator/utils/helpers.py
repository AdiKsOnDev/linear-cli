"""
Utility functions and helpers for Linearator.

Common functions used throughout the application.
"""

import json
import logging
import sys
from datetime import datetime
from typing import Any

from rich.console import Console
from rich.syntax import Syntax
from rich.table import Table


def setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Setup a logger with consistent formatting.

    Args:
        name: Logger name
        level: Logging level

    Returns:
        Configured logger
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if not logger.handlers:
        # Console handler with rich formatting is set up in CLI app
        # This is just for fallback
        handler = logging.StreamHandler(sys.stderr)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


def format_datetime(dt: str | datetime, format_type: str = "human") -> str:
    """
    Format datetime for display.

    Args:
        dt: Datetime string or object
        format_type: Format type ('human', 'iso', 'short')

    Returns:
        Formatted datetime string
    """
    if isinstance(dt, str):
        try:
            # Try to parse ISO format
            dt = datetime.fromisoformat(dt.replace("Z", "+00:00"))
        except ValueError:
            return str(dt)  # Return as string if parsing fails

    if not isinstance(dt, datetime):
        return str(dt)

    if format_type == "human":
        # Human-readable format
        now = datetime.now()
        diff = now - dt

        if diff.days > 7:
            return dt.strftime("%Y-%m-%d")
        elif diff.days > 0:
            return f"{diff.days} days ago"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours} hours ago"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes} minutes ago"
        else:
            return "Just now"

    elif format_type == "iso":
        return dt.isoformat()

    elif format_type == "short":
        return dt.strftime("%m/%d %H:%M")

    else:
        return dt.strftime("%Y-%m-%d %H:%M:%S")


def truncate_text(text: str, max_length: int = 50, suffix: str = "...") -> str:
    """
    Truncate text to maximum length.

    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add when truncated

    Returns:
        Truncated text
    """
    if not text or len(text) <= max_length:
        return text

    return text[: max_length - len(suffix)] + suffix


def format_output(
    data: Any, format_type: str = "table", console: Console | None = None
) -> None:
    """
    Format and display output in various formats.

    Args:
        data: Data to display
        format_type: Output format ('table', 'json', 'yaml')
        console: Rich console instance
    """
    if console is None:
        console = Console()

    if format_type == "json":
        # JSON output
        json_str = json.dumps(data, indent=2, default=str)
        syntax = Syntax(json_str, "json", theme="monokai", line_numbers=False)
        console.print(syntax)

    elif format_type == "yaml":
        # YAML output (fallback to JSON if yaml not available)
        try:
            import yaml

            yaml_str = yaml.dump(data, default_flow_style=False, sort_keys=False)
            syntax = Syntax(yaml_str, "yaml", theme="monokai", line_numbers=False)
            console.print(syntax)
        except ImportError:
            console.print("[yellow]YAML not available, using JSON format[/yellow]")
            format_output(data, "json", console)

    elif format_type == "table" and isinstance(data, list):
        # Table output for list data
        if not data:
            console.print("[yellow]No data to display[/yellow]")
            return

        # Create table from list of dictionaries
        if isinstance(data[0], dict):
            table = Table(show_header=True, header_style="bold blue")

            # Add columns based on first item
            for key in data[0].keys():
                table.add_column(key.replace("_", " ").title())

            # Add rows
            for item in data:
                row = []
                for key in data[0].keys():
                    value = item.get(key, "")
                    if isinstance(value, dict | list):
                        value = str(value)
                    elif isinstance(value, str) and len(value) > 50:
                        value = truncate_text(value)
                    row.append(str(value))
                table.add_row(*row)

            console.print(table)
        else:
            # Simple list
            for item in data:
                console.print(str(item))

    else:
        # Default: print as-is
        console.print(data)


def validate_email(email: str) -> bool:
    """
    Simple email validation.

    Args:
        email: Email to validate

    Returns:
        True if valid, False otherwise
    """
    import re

    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(pattern, email) is not None


def parse_key_value_pairs(pairs: list[str]) -> dict[str, str]:
    """
    Parse key=value pairs from command line.

    Args:
        pairs: List of key=value strings

    Returns:
        Dictionary of parsed pairs
    """
    result = {}
    for pair in pairs:
        if "=" not in pair:
            raise ValueError(f"Invalid key=value pair: {pair}")

        key, value = pair.split("=", 1)
        result[key.strip()] = value.strip()

    return result


def confirm_action(message: str, default: bool = False) -> bool:
    """
    Ask user to confirm an action.

    Args:
        message: Confirmation message
        default: Default value if user just presses enter

    Returns:
        True if confirmed, False otherwise
    """
    from rich.prompt import Confirm

    return Confirm.ask(message, default=default)


def handle_keyboard_interrupt(func: Any) -> Any:
    """
    Decorator to handle keyboard interrupts gracefully.

    Args:
        func: Function to wrap

    Returns:
        Wrapped function
    """

    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return func(*args, **kwargs)
        except KeyboardInterrupt:
            console = Console()
            console.print("\n[yellow]Operation cancelled by user.[/yellow]")
            sys.exit(130)  # Standard exit code for Ctrl+C

    return wrapper


class ProgressTracker:
    """Simple progress tracking for long operations."""

    def __init__(self, total: int, description: str = "Processing"):
        from rich.progress import Progress, TaskID

        self.progress = Progress()
        self.task: TaskID | None = None
        self.total = total
        self.description = description
        self._started = False

    def start(self) -> None:
        """Start the progress tracker."""
        if not self._started:
            self.progress.start()
            self.task = self.progress.add_task(self.description, total=self.total)
            self._started = True

    def update(self, completed: int) -> None:
        """Update progress."""
        if self._started and self.task:
            self.progress.update(self.task, completed=completed)

    def advance(self, amount: int = 1) -> None:
        """Advance progress by amount."""
        if self._started and self.task:
            self.progress.advance(self.task, amount)

    def stop(self) -> None:
        """Stop the progress tracker."""
        if self._started:
            self.progress.stop()
            self._started = False

    def __enter__(self) -> "ProgressTracker":
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        self.stop()
