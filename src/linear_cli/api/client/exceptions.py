"""
Exception classes for Linear API client.

Defines custom exceptions for different types of API errors.
"""

from typing import Any


class LinearAPIError(Exception):
    """Base exception for Linear API errors."""

    pass


class RateLimitError(LinearAPIError):
    """Raised when API rate limit is exceeded."""

    pass


class GraphQLError(LinearAPIError):
    """Raised when GraphQL query returns errors."""

    def __init__(self, message: str, errors: list[dict[str, Any]]):
        super().__init__(message)
        self.errors = errors
