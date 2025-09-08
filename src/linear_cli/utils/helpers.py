"""
Utility functions and helpers for Linearator.

Common functions used throughout the application.
"""

import hashlib
import json
import logging
import re
import sys
import time
import uuid
from collections.abc import Callable, Generator
from datetime import datetime, timedelta
from functools import wraps
from pathlib import Path
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

    if not email or not isinstance(email, str):
        return False
    
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


# Additional helper functions for comprehensive test coverage


def format_date(date_input: str | datetime | None) -> str | None:
    """Format date for display."""
    if date_input is None:
        return "Never"

    if isinstance(date_input, str):
        try:
            dt = datetime.fromisoformat(date_input.replace("Z", "+00:00"))
        except ValueError:
            return "Invalid date"
    elif isinstance(date_input, datetime):
        dt = date_input
    else:
        return None

    return dt.strftime("%Y-%m-%d %H:%M:%S")


def format_relative_time(dt: datetime | str) -> str:
    """Format time relative to now."""
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt.replace("Z", "+00:00"))
        except ValueError:
            return "Invalid time"

    now = datetime.now()
    diff = now - dt

    if diff.days > 0:
        return f"{diff.days} day{'s' if diff.days != 1 else ''} ago"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    else:
        return "Just now"


def parse_date_input(date_str: str) -> datetime | None:
    """Parse various date input formats."""
    if not date_str:
        return None

    date_str = date_str.lower().strip()

    # Handle relative dates
    if date_str == "today":
        return datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    elif date_str == "yesterday":
        return (datetime.now() - timedelta(days=1)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
    elif "ago" in date_str:
        # Simple parsing for "X days ago", "X weeks ago"
        parts = date_str.split()
        if len(parts) >= 3:
            try:
                amount = int(parts[0])
                unit = parts[1]
                if "day" in unit:
                    return datetime.now() - timedelta(days=amount)
                elif "week" in unit:
                    return datetime.now() - timedelta(weeks=amount)
            except (ValueError, IndexError):
                pass

    # Try to parse ISO format
    try:
        return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except ValueError:
        pass

    return None


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe filesystem use."""
    if not filename:
        return "untitled"

    # Remove/replace unsafe characters
    unsafe_chars = ["/", "\\", ":", "*", "?", "<", ">", "|", '"']
    sanitized = filename
    for char in unsafe_chars:
        sanitized = sanitized.replace(char, "_")

    # Truncate to reasonable length
    if len(sanitized) > 255:
        sanitized = sanitized[:252] + "..."

    return sanitized


def truncate_string(text: str, max_length: int) -> str:
    """Truncate string to max length with ellipsis."""
    if not text or len(text) <= max_length:
        return text

    if max_length <= 3:
        return text[:max_length]

    return text[: max_length - 3] + "..."


def validate_uuid(uuid_string: str) -> bool:
    """Validate UUID string."""
    if not uuid_string:
        return False

    try:
        uuid.UUID(uuid_string)
        return True
    except (ValueError, TypeError):
        return False


def deep_merge_dicts(dict1: dict[str, Any], dict2: dict[str, Any]) -> dict[str, Any]:
    """Deep merge two dictionaries."""
    result = dict1.copy()

    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge_dicts(result[key], value)
        else:
            result[key] = value

    return result


def flatten_dict(nested_dict: dict[str, Any], separator: str = ".") -> dict[str, Any]:
    """Flatten nested dictionary."""

    def _flatten(obj: Any, parent_key: str = "") -> dict[str, Any]:
        items: list[tuple[str, Any]] = []
        if isinstance(obj, dict):
            for key, value in obj.items():
                new_key = f"{parent_key}{separator}{key}" if parent_key else key
                items.extend(_flatten(value, new_key).items())
        else:
            return {parent_key: obj}
        return dict(items)

    return _flatten(nested_dict)


def safe_json_loads(json_str: str | None, default: Any = None) -> Any:
    """Safely load JSON string."""
    if not json_str:
        return default

    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError):
        return default


def retry_with_backoff(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: tuple[type[Exception], ...] = (Exception,),
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator for retrying functions with exponential backoff."""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            delay = initial_delay
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        time.sleep(delay)
                        delay *= backoff_factor
                    else:
                        raise e

            if last_exception:
                raise last_exception

        return wrapper

    return decorator


def batch_items(items: list[Any], batch_size: int) -> Generator[list[Any], None, None]:
    """Batch items into chunks of specified size."""
    for i in range(0, len(items), batch_size):
        yield items[i : i + batch_size]


def ensure_list(value: Any) -> list[Any]:
    """Ensure value is a list."""
    if value is None:
        return []
    elif isinstance(value, list):
        return value
    else:
        return [value]


def get_nested_value(data: dict[str, Any], key_path: str, default: Any = None) -> Any:
    """Get nested dictionary value using dot notation."""
    keys = key_path.split(".")
    current = data

    try:
        for key in keys:
            current = current[key]
        return current
    except (KeyError, TypeError):
        return default


def calculate_file_hash(file_path: str | Path, algorithm: str = "sha256") -> str:
    """Calculate hash of file contents."""
    hash_func = getattr(hashlib, algorithm, hashlib.sha256)()

    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_func.update(chunk)

    return hash_func.hexdigest()


def normalize_line_endings(text: str, line_ending: str = "\n") -> str:
    """Normalize line endings in text."""
    # Replace all variations with consistent line ending
    text = text.replace("\r\n", "\n")  # Windows
    text = text.replace("\r", "\n")  # Old Mac

    if line_ending != "\n":
        text = text.replace("\n", line_ending)

    return text
