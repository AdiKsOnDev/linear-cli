"""
Constants for the Linearator application.

Contains priority mappings, color schemes, and other magic numbers used
throughout the application to improve maintainability and reduce duplication.
"""

# Linear Priority Mappings
# Maps Linear priority integers to display text and Rich style colors
PRIORITY_LEVELS: dict[int, tuple[str, str]] = {
    0: ("None", "dim"),
    1: ("Low", "blue"),
    2: ("Normal", "white"),
    3: ("High", "yellow"),
    4: ("Urgent", "red bold"),
}

# Default priority when None or invalid priority is provided
DEFAULT_PRIORITY = 0

# Linear State Enum Mappings
# Maps numeric state values to common Linear state names for user convenience
# This provides a consistent interface across teams with different state names
#
# BACKWARD COMPATIBILITY DESIGN:
# This mapping system is designed to work alongside existing text-based state input,
# not replace it. Users can continue using exact state names (case-insensitive)
# while also having the option of faster numeric shortcuts.
#
# CROSS-TEAM STANDARDIZATION:
# Different Linear teams often use different state names (e.g., "To Do" vs "Todo" vs "Backlog").
# These numeric mappings provide a standardized interface that works across all teams
# by mapping to the most common state name patterns in Linear workspaces.
#
# IMPLEMENTATION STRATEGY:
# - State resolution first checks if input is numeric (0-6)
# - If numeric, maps to standard name and searches team states for case-insensitive match
# - If text, performs direct case-insensitive search in team states
# - Provides helpful tips when text input fails to encourage numeric adoption
# - Graceful fallback ensures no functionality loss for existing users
STATE_MAPPINGS: dict[int, tuple[str, str]] = {
    0: ("Canceled", "dim"),
    1: ("Backlog", "blue"),
    2: ("Todo", "yellow"),
    3: ("In Progress", "green"),
    4: ("In Review", "orange"),
    5: ("Done", "bright_green bold"),
    6: ("Duplicate", "dim"),
}

# Default state when None or invalid state is provided
DEFAULT_STATE = 1

# Color Pattern Mappings for Hex to Rich Color Approximation
# Used to convert Linear's hex colors to terminal-friendly Rich color names
COLOR_PATTERNS: dict[str, str] = {
    "ff_in_first_three": "red",  # Red-ish colors
    "00ff_green": "green",  # Green-ish colors
    "0f0_green": "green",  # Green shorthand
    "ff0_yellow": "yellow",  # Yellow colors
    "ffff00_yellow": "yellow",  # Yellow hex
    "blue_pattern": "blue",  # Blue-ish colors
}

# Default color style for unknown/invalid colors
DEFAULT_COLOR_STYLE = "dim"

# Default fallback color for states
DEFAULT_STATE_COLOR = "#808080"

# Linear API Constants
LINEAR_API_RATE_LIMIT_WINDOW = 60  # Rate limit reset window in seconds
DEFAULT_CACHE_TTL = 300  # Default cache time-to-live in seconds
DEFAULT_API_TIMEOUT = 30  # Default API request timeout in seconds

# CLI Display Constants
DEFAULT_ISSUE_LIMIT = 50  # Default number of issues to fetch
MAX_ISSUE_LIMIT = 250  # Maximum issues allowed in single request
DEFAULT_LABEL_LIMIT = 100  # Default number of labels to fetch

# OAuth Constants
OAUTH_REDIRECT_URI = "http://localhost:8080/callback"
OAUTH_CALLBACK_PORT = 8080

# Team ID Heuristics - Used to distinguish team IDs from team keys
TEAM_ID_PREFIX = "team_"
TEAM_ID_MIN_LENGTH = 20  # Team IDs are typically longer than keys

# Color Validation
HEX_COLOR_PREFIX = "#"
HEX_COLOR_LENGTH = 7  # Including the # prefix
