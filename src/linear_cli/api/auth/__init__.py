"""
Authentication module for Linear API.

Provides OAuth 2.0 and API key authentication with secure credential storage.
"""

from .core import LinearAuthenticator, TokenExpiredError
from .oauth import OAuthFlowError, OAuthFlowManager
from .storage import AuthenticationError, CredentialStorage

__all__ = [
    "LinearAuthenticator",
    "CredentialStorage",
    "OAuthFlowManager",
    "AuthenticationError",
    "TokenExpiredError",
    "OAuthFlowError",
]
