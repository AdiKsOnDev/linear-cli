"""
Unit tests for authentication module.

Tests the LinearAuthenticator and CredentialStorage classes.
"""

import urllib.parse
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

import httpx
import pytest

from src.linear-cli.api.auth import (
    AuthenticationError,
    LinearAuthenticator,
    OAuthFlowError,
)


class TestCredentialStorage:
    """Test cases for CredentialStorage class."""

    def test_init(self, mock_credential_storage):
        """Test CredentialStorage initialization."""
        assert mock_credential_storage.user_id == "test_user"
        assert mock_credential_storage.SERVICE_NAME == "linear-cli"

    def test_store_and_retrieve_credentials(self, mock_credential_storage):
        """Test storing and retrieving credentials."""
        test_credentials = {
            "access_token": "test_token",
            "refresh_token": "test_refresh",
            "expires_at": "2024-01-01T00:00:00",
        }

        # Store credentials
        mock_credential_storage.store_credentials(test_credentials)

        # Retrieve credentials
        retrieved = mock_credential_storage.retrieve_credentials()

        assert retrieved is not None
        assert retrieved["access_token"] == "test_token"
        assert retrieved["refresh_token"] == "test_refresh"
        assert retrieved["expires_at"] == "2024-01-01T00:00:00"

    def test_retrieve_nonexistent_credentials(self, mock_credential_storage):
        """Test retrieving credentials that don't exist."""
        result = mock_credential_storage.retrieve_credentials()
        assert result is None

    def test_delete_credentials(self, mock_credential_storage):
        """Test deleting stored credentials."""
        # Store credentials first
        test_credentials = {"access_token": "test_token"}
        mock_credential_storage.store_credentials(test_credentials)

        # Verify they exist
        assert mock_credential_storage.retrieve_credentials() is not None

        # Delete credentials
        mock_credential_storage.delete_credentials()

        # Verify they're gone
        assert mock_credential_storage.retrieve_credentials() is None


class TestLinearAuthenticator:
    """Test cases for LinearAuthenticator class."""

    def test_init(self, authenticator):
        """Test LinearAuthenticator initialization."""
        assert authenticator.client_id == "test_client_id"
        assert authenticator.client_secret == "test_client_secret"
        assert authenticator.redirect_uri == "http://localhost:8080/callback"
        assert authenticator._access_token is None
        assert not authenticator.is_authenticated

    def test_api_key_authentication_success(self, authenticator):
        """Test successful API key authentication."""
        with patch.object(authenticator, "_validate_api_key", return_value=True):
            authenticator.authenticate_with_api_key("test_api_key")

            assert authenticator._access_token == "test_api_key"
            assert authenticator._refresh_token is None
            assert authenticator._token_expires_at is None
            assert authenticator.is_authenticated

    def test_api_key_authentication_failure(self, authenticator):
        """Test API key authentication failure."""
        with patch.object(authenticator, "_validate_api_key", return_value=False):
            with pytest.raises(AuthenticationError, match="Invalid API key"):
                authenticator.authenticate_with_api_key("invalid_key")

    def test_validate_api_key_success(self, authenticator):
        """Test API key validation success."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": {"viewer": {"id": "test"}}}

        with patch("httpx.Client") as mock_client:
            mock_client.return_value.__enter__.return_value.post.return_value = (
                mock_response
            )

            result = authenticator._validate_api_key("valid_key")
            assert result is True

    def test_validate_api_key_failure(self, authenticator):
        """Test API key validation failure."""
        mock_response = Mock()
        mock_response.status_code = 401

        with patch("httpx.Client") as mock_client:
            mock_client.return_value.__enter__.return_value.post.return_value = (
                mock_response
            )

            result = authenticator._validate_api_key("invalid_key")
            assert result is False

    def test_start_oauth_flow_success(self, authenticator):
        """Test starting OAuth flow."""
        auth_url, state = authenticator.start_oauth_flow()

        assert "linear.app/oauth/authorize" in auth_url
        assert f"client_id={authenticator.client_id}" in auth_url
        assert (
            f"redirect_uri={urllib.parse.quote(authenticator.redirect_uri, safe='')}"
            in auth_url
        )
        assert "response_type=code" in auth_url
        assert f"state={state}" in auth_url
        assert len(state) > 20  # State should be long random string

    def test_start_oauth_flow_no_client_id(self):
        """Test starting OAuth flow without client ID."""
        authenticator = LinearAuthenticator()

        with pytest.raises(OAuthFlowError, match="OAuth client_id is required"):
            authenticator.start_oauth_flow()

    def test_complete_oauth_flow_success(self, authenticator, mock_http_responses):
        """Test completing OAuth flow successfully."""
        mock_response = Mock()
        mock_response.json.return_value = mock_http_responses["token_success"]

        with patch("httpx.Client") as mock_client:
            mock_client.return_value.__enter__.return_value.post.return_value = (
                mock_response
            )

            authenticator.complete_oauth_flow("test_code", "test_state", "test_state")

            assert authenticator._access_token == "test_access_token"
            assert authenticator._refresh_token == "test_refresh_token"
            assert authenticator._token_expires_at is not None
            assert authenticator.is_authenticated

    def test_complete_oauth_flow_invalid_state(self, authenticator):
        """Test OAuth flow with invalid state."""
        with pytest.raises(OAuthFlowError, match="Invalid state parameter"):
            authenticator.complete_oauth_flow("code", "wrong_state", "expected_state")

    def test_complete_oauth_flow_http_error(self, authenticator):
        """Test OAuth flow with HTTP error."""
        with patch("httpx.Client") as mock_client:
            mock_client.return_value.__enter__.return_value.post.side_effect = (
                httpx.HTTPError("Network error")
            )

            with pytest.raises(OAuthFlowError, match="Token exchange failed"):
                authenticator.complete_oauth_flow("code", "state", "state")

    def test_token_expiration_check(self, authenticator):
        """Test token expiration checking."""
        # Set token that expires in past
        authenticator._access_token = "test_token"
        authenticator._token_expires_at = datetime.now() - timedelta(hours=1)

        assert authenticator._is_token_expired()
        assert not authenticator.is_authenticated

    def test_token_not_expired(self, authenticator):
        """Test token that hasn't expired."""
        # Set token that expires in future
        authenticator._access_token = "test_token"
        authenticator._token_expires_at = datetime.now() + timedelta(hours=1)

        assert not authenticator._is_token_expired()
        assert authenticator.is_authenticated

    def test_get_access_token_valid(self, authenticator):
        """Test getting valid access token."""
        authenticator._access_token = "test_token"
        authenticator._token_expires_at = datetime.now() + timedelta(hours=1)

        token = authenticator.get_access_token()
        assert token == "test_token"

    def test_get_access_token_expired_with_refresh(
        self, authenticator, mock_http_responses
    ):
        """Test getting access token when expired but refresh available."""
        # Set expired token with refresh token
        authenticator._access_token = "old_token"
        authenticator._refresh_token = "refresh_token"
        authenticator._token_expires_at = datetime.now() - timedelta(hours=1)

        # Mock successful refresh
        mock_response = Mock()
        mock_response.json.return_value = {
            "access_token": "new_token",
            "expires_in": 3600,
        }

        with patch("httpx.Client") as mock_client:
            mock_client.return_value.__enter__.return_value.post.return_value = (
                mock_response
            )

            token = authenticator.get_access_token()
            assert token == "new_token"

    def test_get_access_token_refresh_failed(self, authenticator):
        """Test getting access token when refresh fails."""
        # Set expired token with refresh token
        authenticator._access_token = "old_token"
        authenticator._refresh_token = "refresh_token"
        authenticator._token_expires_at = datetime.now() - timedelta(hours=1)

        # Mock failed refresh
        with patch("httpx.Client") as mock_client:
            mock_client.return_value.__enter__.return_value.post.side_effect = (
                httpx.HTTPError("Refresh failed")
            )

            token = authenticator.get_access_token()
            assert token is None

    def test_refresh_token_success(self, authenticator, mock_http_responses):
        """Test successful token refresh."""
        authenticator._refresh_token = "refresh_token"

        mock_response = Mock()
        mock_response.json.return_value = {
            "access_token": "new_access_token",
            "refresh_token": "new_refresh_token",
            "expires_in": 3600,
        }

        with patch("httpx.Client") as mock_client:
            mock_client.return_value.__enter__.return_value.post.return_value = (
                mock_response
            )

            authenticator.refresh_token()

            assert authenticator._access_token == "new_access_token"
            assert authenticator._refresh_token == "new_refresh_token"
            assert authenticator._token_expires_at > datetime.now()

    def test_refresh_token_no_refresh_token(self, authenticator):
        """Test token refresh without refresh token."""
        with pytest.raises(AuthenticationError, match="No refresh token available"):
            authenticator.refresh_token()

    def test_refresh_token_http_error(self, authenticator):
        """Test token refresh with HTTP error."""
        authenticator._refresh_token = "refresh_token"

        with patch("httpx.Client") as mock_client:
            mock_client.return_value.__enter__.return_value.post.side_effect = (
                httpx.HTTPError("Network error")
            )

            with pytest.raises(AuthenticationError, match="Token refresh failed"):
                authenticator.refresh_token()

    def test_logout(self, authenticator):
        """Test logout functionality."""
        # Set up authenticated state
        authenticator._access_token = "test_token"
        authenticator._refresh_token = "refresh_token"
        authenticator._token_expires_at = datetime.now() + timedelta(hours=1)

        # Logout
        authenticator.logout()

        assert authenticator._access_token is None
        assert authenticator._refresh_token is None
        assert authenticator._token_expires_at is None
        assert not authenticator.is_authenticated

    def test_get_token_info_authenticated(self, authenticator):
        """Test getting token info when authenticated."""
        authenticator._access_token = "test_token"
        authenticator._refresh_token = "refresh_token"
        expires_at = datetime.now() + timedelta(hours=1)
        authenticator._token_expires_at = expires_at

        info = authenticator.get_token_info()

        assert info["is_authenticated"] is True
        assert info["has_access_token"] is True
        assert info["has_refresh_token"] is True
        assert info["expires_at"] == expires_at.isoformat()
        assert info["is_expired"] is False

    def test_get_token_info_not_authenticated(self, authenticator):
        """Test getting token info when not authenticated."""
        info = authenticator.get_token_info()

        assert info["is_authenticated"] is False
        assert info["has_access_token"] is False
        assert info["has_refresh_token"] is False
        assert info["expires_at"] is None

    def test_jwt_token_decode(self, authenticator):
        """Test JWT token decoding in token info."""
        # Mock JWT token (header.payload.signature format)
        jwt_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ1c2VyXzEyMyIsImlhdCI6MTYwOTQ1OTIwMCwiZXhwIjoxNjA5NDYyODAwfQ.signature"
        authenticator._access_token = jwt_token

        with patch("jwt.decode") as mock_decode:
            mock_decode.return_value = {
                "sub": "user_123",
                "iat": 1609459200,
                "exp": 1609462800,
            }

            info = authenticator.get_token_info()

            assert info["token_type"] == "jwt"
            assert info["user_id"] == "user_123"
            assert info["issued_at"] == 1609459200
            assert info["expires_at_jwt"] == 1609462800

    def test_api_key_token_type(self, authenticator):
        """Test token type detection for API keys."""
        # API keys don't have JWT format
        authenticator._access_token = "lin_api_key_12345"

        info = authenticator.get_token_info()
        assert info["token_type"] == "api_key"

    def test_credential_persistence(self, authenticator):
        """Test that credentials are saved and loaded."""
        # Authenticate with API key
        with patch.object(authenticator, "_validate_api_key", return_value=True):
            authenticator.authenticate_with_api_key("test_api_key")

        # Create new authenticator instance (should load stored credentials)
        new_auth = LinearAuthenticator(
            client_id="test_client_id",
            client_secret="test_client_secret",
            storage=authenticator.storage,
        )

        # Check that credentials were loaded
        assert new_auth._access_token == "test_api_key"
        assert new_auth.is_authenticated
