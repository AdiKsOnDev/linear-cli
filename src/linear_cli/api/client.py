"""
Linear GraphQL API client (backward compatibility module).

This module maintains backward compatibility by re-exporting all client classes
from the modular client package.
"""

# Re-export everything from the modular client for backward compatibility
from .client import (
    GraphQLError,
    LinearAPIError,
    LinearClient,
    RateLimiter,
    RateLimitError,
    ResponseCache,
)

__all__ = [
    "LinearClient",
    "LinearAPIError",
    "RateLimitError",
    "GraphQLError",
    "RateLimiter",
    "ResponseCache",
]
