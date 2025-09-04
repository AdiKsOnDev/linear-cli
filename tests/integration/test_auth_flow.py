"""
Integration tests for authentication flow.

Tests the complete authentication workflow including OAuth and API key flows.
"""

from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner

from linear_cli.api.auth import AuthenticationError, LinearAuthenticator
from linear_cli.api.client import LinearClient
from linear_cli.cli.app import main
from linear_cli.config.manager import LinearConfig


@pytest.mark.integration
class TestAuthenticationFlow:
    """Integration tests for authentication workflow."""

    def test_api_key_authentication_flow(self, authenticator, mock_credential_storage):
        """Test complete API key authentication flow."""
        # Mock successful API validation
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {
                "viewer": {
                    "id": "user_123",
                    "name": "Test User",
                    "email": "test@example.com",
                }
            }
        }

        with patch("httpx.Client") as mock_client:
            mock_client.return_value.__enter__.return_value.post.return_value = (
                mock_response
            )

            # Authenticate with API key
            authenticator.authenticate_with_api_key("lin_api_valid_key")

            # Verify authentication
            assert authenticator.is_authenticated
            assert authenticator.get_access_token() == "lin_api_valid_key"

            # Verify credentials were stored
            stored_creds = mock_credential_storage.retrieve_credentials()
            assert stored_creds is not None
            assert stored_creds["access_token"] == "lin_api_valid_key"

    def test_oauth_flow_complete(self, authenticator, mock_credential_storage):
        """Test complete OAuth authentication flow."""
        # Mock token exchange response
        token_response = Mock()
        token_response.status_code = 200
        token_response.json.return_value = {
            "access_token": "oauth_access_token",
            "refresh_token": "oauth_refresh_token",
            "token_type": "Bearer",
            "expires_in": 3600,
        }

        with patch("httpx.Client") as mock_client:
            mock_client.return_value.__enter__.return_value.post.return_value = (
                token_response
            )

            # Start OAuth flow
            auth_url, state = authenticator.start_oauth_flow()
            assert "client_id=test_client_id" in auth_url

            # Complete OAuth flow
            authenticator.complete_oauth_flow("auth_code", state, state)

            # Verify authentication
            assert authenticator.is_authenticated
            assert authenticator.get_access_token() == "oauth_access_token"

            # Verify credentials were stored
            stored_creds = mock_credential_storage.retrieve_credentials()
            assert stored_creds is not None
            assert stored_creds["access_token"] == "oauth_access_token"
            assert stored_creds["refresh_token"] == "oauth_refresh_token"

    def test_token_refresh_flow(self, authenticator, mock_credential_storage):
        """Test token refresh workflow."""
        # Set up initial OAuth tokens
        token_response = Mock()
        token_response.status_code = 200
        token_response.json.return_value = {
            "access_token": "initial_token",
            "refresh_token": "initial_refresh",
            "expires_in": 3600,
        }

        with patch("httpx.Client") as mock_client:
            mock_client.return_value.__enter__.return_value.post.return_value = (
                token_response
            )

            # Complete initial OAuth flow
            auth_url, state = authenticator.start_oauth_flow()
            authenticator.complete_oauth_flow("auth_code", state, state)

            # Mock refresh token response
            refresh_response = Mock()
            refresh_response.status_code = 200
            refresh_response.json.return_value = {
                "access_token": "refreshed_token",
                "refresh_token": "new_refresh_token",
                "expires_in": 3600,
            }

            mock_client.return_value.__enter__.return_value.post.return_value = (
                refresh_response
            )

            # Refresh token
            authenticator.refresh_token()

            # Verify new tokens
            assert authenticator.get_access_token() == "refreshed_token"
            assert authenticator._refresh_token == "new_refresh_token"

            # Verify credentials were updated
            stored_creds = mock_credential_storage.retrieve_credentials()
            assert stored_creds["access_token"] == "refreshed_token"
            assert stored_creds["refresh_token"] == "new_refresh_token"

    def test_credential_persistence_across_sessions(self, temp_config_dir, mock_config):
        """Test that credentials persist across authenticator instances."""
        # First authenticator instance
        auth1 = LinearAuthenticator(
            client_id=mock_config.client_id,
            client_secret=mock_config.client_secret,
        )

        # Mock API key validation
        with patch.object(auth1, "_validate_api_key", return_value=True):
            auth1.authenticate_with_api_key("persistent_key")

        assert auth1.is_authenticated

        # Create new authenticator instance (simulating app restart)
        auth2 = LinearAuthenticator(
            client_id=mock_config.client_id,
            client_secret=mock_config.client_secret,
        )

        # Should automatically load stored credentials
        assert auth2.is_authenticated
        assert auth2.get_access_token() == "persistent_key"

    def test_logout_clears_all_credentials(
        self, authenticator, mock_credential_storage
    ):
        """Test that logout completely clears all stored credentials."""
        # Authenticate first
        with patch.object(authenticator, "_validate_api_key", return_value=True):
            authenticator.authenticate_with_api_key("test_key")

        assert authenticator.is_authenticated
        assert mock_credential_storage.retrieve_credentials() is not None

        # Logout
        authenticator.logout()

        # Verify complete cleanup
        assert not authenticator.is_authenticated
        assert authenticator.get_access_token() is None
        assert mock_credential_storage.retrieve_credentials() is None


@pytest.mark.integration
@pytest.mark.slow
class TestCLIAuthCommands:
    """Integration tests for CLI authentication commands."""

    def test_auth_status_unauthenticated(self, temp_config_dir):
        """Test auth status command when not authenticated."""
        runner = CliRunner()

        with (
            patch("src.linear-cli.cli.app.ConfigManager") as mock_cm,
            patch("src.linear-cli.api.auth.core.CredentialStorage") as mock_storage,
        ):
            # Mock empty credentials
            mock_storage.return_value.retrieve_credentials.return_value = None

            mock_cm.return_value.config_dir = temp_config_dir
            mock_cm.return_value.load_config.return_value = LinearConfig(
                debug=False,
                verbose=False,
                client_id="test_id",
                client_secret="test_secret",
                api_url="https://api.linear.app/graphql",
                timeout=30,
                max_retries=3,
                cache_ttl=300,
                cache_dir=temp_config_dir / "cache",
            )

            result = runner.invoke(
                main, ["--config-dir", str(temp_config_dir), "auth", "status"]
            )

            assert result.exit_code == 0
            assert "Not authenticated" in result.output

    def test_auth_login_api_key_success(self, temp_config_dir):
        """Test successful API key login via CLI."""
        runner = CliRunner()

        # Mock successful API validation
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": {"viewer": {"name": "Test User"}}}

        with (
            patch("httpx.Client") as mock_client,
            patch("src.linear-cli.cli.app.ConfigManager") as mock_cm,
            patch("src.linear-cli.api.client.LinearClient.get_viewer") as mock_viewer,
        ):
            mock_client.return_value.__enter__.return_value.post.return_value = (
                mock_response
            )
            mock_viewer.return_value = {"name": "Test User"}  # Mock the viewer response

            mock_cm.return_value.config_dir = temp_config_dir
            mock_cm.return_value.load_config.return_value = LinearConfig(
                debug=False,
                verbose=False,
                client_id="test_id",
                client_secret="test_secret",
                api_url="https://api.linear.app/graphql",
                timeout=30,
                max_retries=3,
                cache_ttl=300,
                cache_dir=temp_config_dir / "cache",
            )

            result = runner.invoke(
                main,
                [
                    "--config-dir",
                    str(temp_config_dir),
                    "auth",
                    "login",
                    "--api-key",
                    "test_key",
                ],
            )

            # Debug output
            if result.exit_code != 0:
                print(f"Exit code: {result.exit_code}")
                print(f"Output: {result.output}")
                print(f"Exception: {result.exception}")

            assert result.exit_code == 0
            assert "Successfully authenticated" in result.output
            assert "Connected as Test User" in result.output

    def test_auth_login_api_key_failure(self, temp_config_dir):
        """Test failed API key login via CLI."""
        runner = CliRunner()

        # Mock failed API validation
        mock_response = Mock()
        mock_response.status_code = 401

        with (
            patch("httpx.Client") as mock_client,
            patch("src.linear-cli.cli.app.ConfigManager") as mock_cm,
        ):
            mock_client.return_value.__enter__.return_value.post.return_value = (
                mock_response
            )
            mock_cm.return_value.config_dir = temp_config_dir
            mock_cm.return_value.load_config.return_value = LinearConfig(
                debug=False,
                verbose=False,
                client_id="test_id",
                client_secret="test_secret",
                api_url="https://api.linear.app/graphql",
                timeout=30,
                max_retries=3,
                cache_ttl=300,
                cache_dir=temp_config_dir / "cache",
            )

            result = runner.invoke(
                main,
                [
                    "--config-dir",
                    str(temp_config_dir),
                    "auth",
                    "login",
                    "--api-key",
                    "invalid_key",
                ],
            )

            assert result.exit_code == 1
            assert "Authentication failed" in result.output

    def test_auth_logout_success(self, temp_config_dir):
        """Test successful logout via CLI."""
        runner = CliRunner()

        with patch("src.linear-cli.cli.app.ConfigManager") as mock_cm:
            mock_cm.return_value.config_dir = temp_config_dir
            mock_cm.return_value.load_config.return_value = LinearConfig(
                debug=False,
                verbose=False,
                client_id="test_id",
                client_secret="test_secret",
                api_url="https://api.linear.app/graphql",
                timeout=30,
                max_retries=3,
                cache_ttl=300,
                cache_dir=temp_config_dir / "cache",
            )

            result = runner.invoke(
                main, ["--config-dir", str(temp_config_dir), "auth", "logout"]
            )

            assert result.exit_code == 0
            assert "Successfully logged out" in result.output


@pytest.mark.integration
class TestLinearClientAuthentication:
    """Integration tests for LinearClient with authentication."""

    @pytest.mark.asyncio
    async def test_client_with_valid_auth(self, mock_config, authenticator):
        """Test LinearClient with valid authentication."""
        # Set up authenticated state
        with patch.object(authenticator, "_validate_api_key", return_value=True):
            authenticator.authenticate_with_api_key("valid_key")

        client = LinearClient(
            config=mock_config,
            authenticator=authenticator,
            enable_cache=False,
        )

        # Mock GraphQL response
        mock_response = {
            "viewer": {
                "id": "user_123",
                "name": "Test User",
                "email": "test@example.com",
            }
        }

        with patch.object(client, "execute_query", return_value=mock_response):
            result = await client.get_viewer()

            assert result["id"] == "user_123"
            assert result["name"] == "Test User"

    @pytest.mark.asyncio
    async def test_client_with_invalid_auth(self, mock_config, authenticator):
        """Test LinearClient with invalid authentication."""
        # Don't authenticate - should raise error
        client = LinearClient(
            config=mock_config,
            authenticator=authenticator,
            enable_cache=False,
        )

        with pytest.raises(AuthenticationError, match="No valid access token"):
            await client.get_viewer()

    @pytest.mark.asyncio
    async def test_client_auth_refresh_on_401(self, mock_config, authenticator):
        """Test that client attempts token refresh on 401 errors."""
        # Set up OAuth authentication with refresh token
        authenticator._access_token = "expired_token"
        authenticator._refresh_token = "refresh_token"
        authenticator.client_id = "test_client_id"
        authenticator.client_secret = "test_client_secret"

        # Mock refresh token success
        refresh_response = Mock()
        refresh_response.status_code = 200
        refresh_response.json.return_value = {
            "access_token": "new_token",
            "expires_in": 3600,
        }

        with patch("httpx.Client") as mock_client:
            mock_client.return_value.__enter__.return_value.post.return_value = (
                refresh_response
            )

            # Test direct refresh token functionality
            authenticator.refresh_token()

            assert authenticator._access_token == "new_token"
