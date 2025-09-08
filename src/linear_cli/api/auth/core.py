"""
Core authentication module for Linear API.

Provides unified interface for OAuth and API key authentication with token management.
"""

import logging
import os
from datetime import datetime, timedelta
from typing import Any

import httpx

from .oauth import OAuthFlowManager
from .storage import AuthenticationError, CredentialStorage

logger = logging.getLogger(__name__)


class TokenExpiredError(AuthenticationError):
    """Raised when an access token has expired."""

    pass


class LinearAuthenticator:
    """
    Handles authentication with Linear API.

    Supports both OAuth 2.0 flow and direct API key authentication.
    Manages token refresh and secure storage.
    """

    def __init__(
        self,
        client_id: str | None = None,
        client_secret: str | None = None,
        redirect_uri: str = "http://localhost:8080/callback",
        storage: CredentialStorage | None = None,
    ):
        """
        Initialize the authenticator.

        Args:
            client_id: OAuth client ID
            client_secret: OAuth client secret
            redirect_uri: OAuth redirect URI
            storage: Credential storage instance
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.storage = storage or CredentialStorage()

        # Initialize OAuth flow manager
        self._oauth_manager = OAuthFlowManager(
            client_id=client_id, client_secret=client_secret, redirect_uri=redirect_uri
        )

        self._access_token: str | None = None
        self._refresh_token: str | None = None
        self._token_expires_at: datetime | None = None

        # Load existing credentials
        self._load_stored_credentials()

    def _load_stored_credentials(self) -> None:
        """Load credentials from secure storage or environment variable."""
        credentials = self.storage.retrieve_credentials()
        if credentials:
            self._access_token = credentials.get("access_token")
            self._refresh_token = credentials.get("refresh_token")

            expires_at = credentials.get("expires_at")
            if expires_at:
                self._token_expires_at = datetime.fromisoformat(expires_at)

            logger.debug("Loaded stored credentials")
        else:
            # Check for API key in environment variable
            api_key = os.getenv("LINEAR_API_KEY")
            if api_key:
                # Validate the API key before using it
                if self._validate_api_key(api_key):
                    self._access_token = api_key
                    self._refresh_token = None
                    self._token_expires_at = None  # API keys don't expire
                    logger.info(
                        "Loaded API key from LINEAR_API_KEY environment variable"
                    )
                else:
                    logger.warning(
                        "Invalid API key found in LINEAR_API_KEY environment variable"
                    )

    def _save_credentials(self) -> None:
        """Save credentials to secure storage."""
        credentials = {
            "access_token": self._access_token,
            "refresh_token": self._refresh_token,
            "expires_at": (
                self._token_expires_at.isoformat() if self._token_expires_at else None
            ),
            "stored_at": datetime.now().isoformat(),
        }
        self.storage.store_credentials(credentials)

    @property
    def is_authenticated(self) -> bool:
        """Check if user is currently authenticated."""
        return self._access_token is not None and not self._is_token_expired()

    def _is_token_expired(self) -> bool:
        """
        Check if access token has expired with safety buffer.

        Includes a 5-minute buffer before actual expiration to prevent
        race conditions during API calls and allow time for token refresh.

        Returns:
            bool: True if token is expired or will expire within buffer time
        """
        if not self._token_expires_at:
            return False

        # 5-minute buffer prevents race conditions during high-frequency API usage
        buffer_time = timedelta(minutes=5)
        return datetime.now() >= (self._token_expires_at - buffer_time)

    def get_access_token(self) -> str | None:
        """
        Get current access token.

        Returns:
            Current access token or None if not authenticated
        """
        if self._is_token_expired() and self._refresh_token:
            try:
                self.refresh_token()
            except Exception as e:
                logger.warning(f"Failed to refresh token: {e}")
                return None

        return self._access_token

    def authenticate_with_api_key(self, api_key: str) -> None:
        """
        Authenticate using a Linear API key.

        Args:
            api_key: Linear API key

        Raises:
            AuthenticationError: If API key is invalid
        """
        # Validate API key by making a test request - minimal API call that confirms both authentication and basic access
        if not self._validate_api_key(api_key):
            raise AuthenticationError("Invalid API key")

        self._access_token = api_key
        self._refresh_token = None
        self._token_expires_at = None  # API keys don't expire
        self._save_credentials()

        logger.info("Authenticated with API key")

    def _validate_api_key(self, api_key: str) -> bool:
        """
        Validate API key by making a test request to Linear API.

        Args:
            api_key: API key to validate

        Returns:
            True if valid, False otherwise
        """
        try:
            # Validate by calling viewer query - minimal API call that confirms both authentication and basic API access
            query = "query { viewer { id name } }"
            headers = {
                "Authorization": api_key,
                "Content-Type": "application/json",
            }
            data = {"query": query}

            with httpx.Client(timeout=10) as client:
                response = client.post(
                    "https://api.linear.app/graphql", headers=headers, json=data
                )

                if response.status_code == 200:
                    result = response.json()
                    return "errors" not in result and "data" in result

                return False
        except Exception as e:
            logger.warning(f"API key validation failed: {e}")
            return False

    def start_oauth_flow(self) -> tuple[str, str]:
        """Start OAuth 2.0 authorization flow."""
        return self._oauth_manager.start_oauth_flow()

    def complete_oauth_flow(self, code: str, state: str, expected_state: str) -> None:
        """
        Complete OAuth 2.0 flow by exchanging code for token.

        Args:
            code: Authorization code from callback
            state: State parameter from callback
            expected_state: Expected state value for validation

        Raises:
            OAuthFlowError: If OAuth flow fails
        """
        access_token, refresh_token, expires_at = (
            self._oauth_manager.complete_oauth_flow(code, state, expected_state)
        )

        self._access_token = access_token
        self._refresh_token = refresh_token
        self._token_expires_at = expires_at

        self._save_credentials()
        logger.info("OAuth flow completed successfully")

    def refresh_token(self) -> None:
        """
        Refresh the access token using the refresh token.

        Raises:
            AuthenticationError: If token refresh fails
        """
        if not self._refresh_token:
            raise AuthenticationError("No refresh token available")

        access_token, refresh_token, expires_at = (
            self._oauth_manager.refresh_access_token(self._refresh_token)
        )

        self._access_token = access_token
        self._refresh_token = refresh_token
        self._token_expires_at = expires_at

        self._save_credentials()
        logger.info("Token refreshed successfully")

    def logout(self) -> None:
        """Logout user and clear stored credentials."""
        self._access_token = None
        self._refresh_token = None
        self._token_expires_at = None
        self.storage.delete_credentials()
        logger.info("User logged out")

    def get_token_info(self) -> dict[str, Any]:
        """
        Get information about current authentication state.

        Returns:
            Dictionary with token information
        """
        info = {
            "is_authenticated": self.is_authenticated,
            "has_access_token": self._access_token is not None,
            "has_refresh_token": self._refresh_token is not None,
            "expires_at": (
                self._token_expires_at.isoformat() if self._token_expires_at else None
            ),
            "is_expired": self._is_token_expired(),
        }

        # Determine token type based on token format
        if self._access_token:
            if (
                self._access_token.count(".") == 2
            ):  # JWT format has 3 parts separated by dots
                info["token_type"] = "jwt"
                # Try to decode JWT for additional info
                try:
                    import jwt

                    decoded = jwt.decode(
                        self._access_token, options={"verify_signature": False}
                    )
                    # Extract standard JWT fields
                    if "sub" in decoded:
                        info["user_id"] = decoded["sub"]
                    if "iat" in decoded:
                        info["issued_at"] = decoded["iat"]
                    if "exp" in decoded:
                        info["expires_at_jwt"] = decoded["exp"]
                except Exception:
                    pass  # If JWT decode fails, just continue without payload
            else:
                info["token_type"] = "api_key"

        return info
