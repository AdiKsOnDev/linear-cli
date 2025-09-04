"""
Pytest configuration and fixtures for Linearator tests.

Provides common fixtures and test configuration.
"""

import asyncio
import os
import tempfile
from collections.abc import Generator
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from linear_cli.api.auth import CredentialStorage, LinearAuthenticator
from linear_cli.api.client import LinearClient
from linear_cli.config.manager import ConfigManager, LinearConfig


@pytest.fixture
def temp_config_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for configuration files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def mock_config(temp_config_dir: Path) -> LinearConfig:
    """Create a mock configuration for testing."""
    return LinearConfig(
        client_id="test_client_id",
        client_secret="test_client_secret",
        redirect_uri="http://localhost:8080/callback",
        api_url="https://api.linear.app/graphql",
        timeout=30,
        max_retries=3,
        default_team_id="team_test123",
        default_team_key="TEST",
        output_format="table",
        cache_dir=temp_config_dir / "cache",
        cache_ttl=300,
        verbose=False,
        debug=False,
    )


@pytest.fixture
def config_manager(temp_config_dir: Path) -> ConfigManager:
    """Create a ConfigManager instance with temporary directory."""
    return ConfigManager(config_dir=temp_config_dir)


@pytest.fixture
def mock_credential_storage(temp_config_dir: Path) -> CredentialStorage:
    """Create a mock credential storage for testing."""
    # Use temporary directory instead of system keyring
    storage = CredentialStorage("test_user")

    # Mock the keyring operations to use file-based storage for testing
    def mock_get_password(service, username):
        file_path = temp_config_dir / f"{service}_{username}"
        if file_path.exists():
            return file_path.read_text()
        return None

    def mock_set_password(service, username, password):
        file_path = temp_config_dir / f"{service}_{username}"
        file_path.write_text(password)

    def mock_delete_password(service, username):
        file_path = temp_config_dir / f"{service}_{username}"
        if file_path.exists():
            file_path.unlink()

    with (
        patch("keyring.get_password", mock_get_password),
        patch("keyring.set_password", mock_set_password),
        patch("keyring.delete_password", mock_delete_password),
    ):
        yield storage


@pytest.fixture
def authenticator(
    mock_config: LinearConfig, mock_credential_storage: CredentialStorage
) -> LinearAuthenticator:
    """Create a LinearAuthenticator instance for testing."""
    return LinearAuthenticator(
        client_id=mock_config.client_id,
        client_secret=mock_config.client_secret,
        redirect_uri=mock_config.redirect_uri,
        storage=mock_credential_storage,
    )


@pytest.fixture
def mock_linear_client(
    mock_config: LinearConfig, authenticator: LinearAuthenticator
) -> LinearClient:
    """Create a mock LinearClient for testing."""
    client = LinearClient(
        config=mock_config,
        authenticator=authenticator,
        enable_cache=False,  # Disable caching for tests
    )
    return client


@pytest.fixture
def mock_api_responses() -> dict[str, Any]:
    """Mock API responses for testing."""
    return {
        "viewer": {
            "id": "user_test123",
            "name": "Test User",
            "email": "test@example.com",
            "displayName": "Test User",
            "organization": {
                "id": "org_test123",
                "name": "Test Organization",
                "urlKey": "test-org",
            },
        },
        "teams": {
            "nodes": [
                {
                    "id": "team_test123",
                    "name": "Test Team",
                    "key": "TEST",
                    "description": "Test team for development",
                    "private": False,
                    "issueCount": 42,
                    "memberCount": 5,
                }
            ]
        },
        "issues": {
            "nodes": [
                {
                    "id": "issue_test123",
                    "identifier": "TEST-1",
                    "title": "Test Issue",
                    "description": "Test issue description",
                    "state": {
                        "id": "state_test123",
                        "name": "Todo",
                        "type": "unstarted",
                    },
                    "team": {
                        "id": "team_test123",
                        "name": "Test Team",
                        "key": "TEST",
                    },
                }
            ]
        },
    }


@pytest.fixture
def mock_http_responses():
    """Mock HTTP responses for authentication testing."""
    return {
        "token_success": {
            "access_token": "test_access_token",
            "refresh_token": "test_refresh_token",
            "token_type": "Bearer",
            "expires_in": 3600,
        },
        "token_error": {
            "error": "invalid_grant",
            "error_description": "The provided authorization grant is invalid",
        },
        "api_success": {
            "data": {
                "viewer": {
                    "id": "user_test123",
                    "name": "Test User",
                }
            }
        },
        "api_error": {
            "errors": [
                {
                    "message": "Authentication failed",
                    "extensions": {"code": "AUTHENTICATION_ERROR"},
                }
            ]
        },
    }


@pytest.fixture(autouse=True)
def clean_environment():
    """Clean environment variables before each test."""
    env_vars = [
        "LINEAR_ACCESS_TOKEN",
        "LINEAR_CLIENT_ID",
        "LINEAR_CLIENT_SECRET",
        "LINEAR_API_URL",
        "LINEAR_DEFAULT_TEAM_ID",
        "LINEAR_VERBOSE",
        "LINEAR_DEBUG",
    ]

    original_values = {}
    for var in env_vars:
        original_values[var] = os.environ.get(var)
        if var in os.environ:
            del os.environ[var]

    yield

    # Restore original values
    for var, value in original_values.items():
        if value is not None:
            os.environ[var] = value
        elif var in os.environ:
            del os.environ[var]


@pytest.fixture
def event_loop():
    """Create an event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# Pytest configuration
def pytest_configure(config):
    """Configure pytest."""
    config.addinivalue_line("markers", "unit: marks tests as unit tests")
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "slow: marks tests as slow")
    config.addinivalue_line("markers", "auth: marks tests as authentication tests")


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers automatically."""
    for item in items:
        # Add unit marker to tests in unit directory
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)

        # Add integration marker to tests in integration directory
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)

        # Add auth marker to authentication tests
        if "auth" in str(item.fspath) or "auth" in item.name:
            item.add_marker(pytest.mark.auth)
