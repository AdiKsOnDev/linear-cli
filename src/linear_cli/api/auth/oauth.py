"""
OAuth 2.0 flow handling for Linear API authentication.

Implements secure OAuth flow with CSRF protection and token management.
"""

import logging
import secrets
import urllib.parse
from datetime import datetime, timedelta

import httpx

from .storage import AuthenticationError

logger = logging.getLogger(__name__)


class OAuthFlowError(AuthenticationError):
    """Raised when OAuth flow fails."""

    pass


class OAuthFlowManager:
    """
    Manages OAuth 2.0 authentication flow for Linear API.

    Handles the complete OAuth flow including authorization URL generation,
    token exchange, and CSRF protection using state parameters.
    """

    OAUTH_BASE_URL = "https://linear.app/oauth"
    TOKEN_URL = "https://api.linear.app/oauth/token"

    def __init__(
        self,
        client_id: str | None = None,
        client_secret: str | None = None,
        redirect_uri: str = "http://localhost:8080/callback",
    ):
        """
        Initialize OAuth flow manager.

        Args:
            client_id: OAuth client ID
            client_secret: OAuth client secret
            redirect_uri: OAuth redirect URI
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri

    def start_oauth_flow(self) -> tuple[str, str]:
        """
        Start OAuth 2.0 authorization flow.

        Generates authorization URL with CSRF protection state parameter.
        Opens browser to Linear's authorization endpoint where user grants access.

        Returns:
            Tuple of (authorization_url, state) - store state for validation

        Raises:
            OAuthFlowError: If OAuth parameters are missing
        """
        if not self.client_id:
            raise OAuthFlowError("OAuth client_id is required")

        # Generate random state for CSRF protection - prevents authorization code interception attacks
        state = secrets.token_urlsafe(32)

        # Build authorization URL with required OAuth 2.0 parameters
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",  # Authorization code flow
            "state": state,  # CSRF protection
            "scope": "read write",  # Request both read and write permissions
        }

        auth_url = f"{self.OAUTH_BASE_URL}/authorize?" + urllib.parse.urlencode(params)

        logger.info(f"OAuth flow started, state: {state[:8]}...")
        return auth_url, state

    def complete_oauth_flow(
        self, code: str, state: str, expected_state: str
    ) -> tuple[str, str | None, datetime]:
        """
        Complete OAuth 2.0 flow by exchanging authorization code for access token.

        Validates the state parameter to prevent CSRF attacks, then exchanges
        the authorization code for an access token and optional refresh token.

        Args:
            code: Authorization code from callback
            state: State parameter from callback
            expected_state: Expected state value for validation

        Returns:
            Tuple of (access_token, refresh_token, expires_at)

        Raises:
            OAuthFlowError: If OAuth flow fails or state validation fails
        """
        if not self.client_id or not self.client_secret:
            raise OAuthFlowError("OAuth client_id and client_secret are required")

        # Validate state parameter to prevent CSRF attacks
        if state != expected_state:
            raise OAuthFlowError("Invalid state parameter - possible CSRF attack")

        # Exchange authorization code for access token
        token_data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "redirect_uri": self.redirect_uri,
            "grant_type": "authorization_code",
        }

        try:
            # Make token exchange request to Linear's OAuth endpoint
            with httpx.Client(timeout=30) as client:
                response = client.post(self.TOKEN_URL, data=token_data)
                response.raise_for_status()

                token_info = response.json()

                access_token = token_info["access_token"]
                refresh_token = token_info.get(
                    "refresh_token"
                )  # Optional in OAuth spec

                # Calculate token expiration time with 5-minute buffer for safety
                expires_in = token_info.get(
                    "expires_in", 3600
                )  # Default 1 hour if not specified
                expires_at = datetime.now() + timedelta(seconds=expires_in)

                logger.info("OAuth flow completed successfully")
                return access_token, refresh_token, expires_at

        except httpx.HTTPError as e:
            logger.error(f"OAuth token exchange failed: {e}")
            raise OAuthFlowError(f"Token exchange failed: {e}") from e
        except KeyError as e:
            logger.error(f"Invalid token response: missing {e}")
            raise OAuthFlowError(f"Invalid token response: missing {e}") from e

    def refresh_access_token(
        self, refresh_token: str
    ) -> tuple[str, str | None, datetime]:
        """
        Refresh access token using refresh token.

        Exchanges the refresh token for a new access token when the current
        token expires. This allows maintaining authentication without user
        re-authorization.

        Args:
            refresh_token: Valid refresh token

        Returns:
            Tuple of (new_access_token, new_refresh_token, expires_at)

        Raises:
            AuthenticationError: If token refresh fails
        """
        if not self.client_id or not self.client_secret:
            raise AuthenticationError("OAuth credentials required for token refresh")

        refresh_data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        }

        try:
            with httpx.Client(timeout=30) as client:
                response = client.post(self.TOKEN_URL, data=refresh_data)
                response.raise_for_status()

                token_info = response.json()

                access_token = token_info["access_token"]
                new_refresh_token = token_info.get(
                    "refresh_token", refresh_token
                )  # Keep old if no new one

                # Calculate expiration time
                expires_in = token_info.get("expires_in", 3600)
                expires_at = datetime.now() + timedelta(seconds=expires_in)

                logger.info("Token refreshed successfully")
                return access_token, new_refresh_token, expires_at

        except httpx.HTTPError as e:
            logger.error(f"Token refresh failed: {e}")
            raise AuthenticationError(f"Token refresh failed: {e}") from e
