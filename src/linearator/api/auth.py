"""
Authentication module for Linear API.

Supports both OAuth 2.0 flow and direct API key authentication.
Handles token storage, refresh, and validation.

This module has been refactored into separate components:
- auth/storage.py: Secure credential storage
- auth/oauth.py: OAuth 2.0 flow handling
- auth/core.py: Main authentication logic

This file maintains backward compatibility by re-exporting all classes.
"""

# Import all classes from refactored modules for backward compatibility
from .auth.core import LinearAuthenticator, TokenExpiredError
from .auth.oauth import OAuthFlowError, OAuthFlowManager
from .auth.storage import AuthenticationError, CredentialStorage

# Export all classes for backward compatibility
__all__ = [
    "LinearAuthenticator",
    "CredentialStorage",
    "OAuthFlowManager",
    "AuthenticationError",
    "TokenExpiredError",
    "OAuthFlowError",
]
