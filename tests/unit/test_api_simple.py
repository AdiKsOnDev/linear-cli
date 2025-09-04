"""Simple API tests for core functionality."""


from linear_cli.api.client.client import LinearClient
from linear_cli.config.manager import LinearConfig


class TestLinearClientBasics:
    """Test basic LinearClient functionality."""

    def test_client_initialization_with_config(self):
        """Test client initialization with config."""
        config = LinearConfig(access_token="test-token")
        client = LinearClient(config)
        assert client.config == config
        assert client.config.access_token == "test-token"

    def test_config_initialization(self):
        """Test LinearConfig initialization."""
        config = LinearConfig()
        assert config.api_url == "https://api.linear.app/graphql"
        assert config.timeout == 30
        assert config.max_retries == 3
        assert config.output_format == "table"

    def test_config_with_token(self):
        """Test LinearConfig with access token."""
        config = LinearConfig(access_token="test-token-123")
        assert config.access_token == "test-token-123"

    def test_client_has_required_methods(self):
        """Test client has expected methods."""
        config = LinearConfig(access_token="test-token")
        client = LinearClient(config)

        # Check for expected methods
        assert hasattr(client, 'execute_query')
        assert hasattr(client, 'get_teams')
        assert hasattr(client, 'get_issues')
        assert hasattr(client, 'get_users')

    def test_client_config_access(self):
        """Test client configuration access."""
        config = LinearConfig(
            access_token="test-token",
            api_url="https://custom.api.url",
            timeout=60
        )
        client = LinearClient(config)

        assert client.config.access_token == "test-token"
        assert client.config.api_url == "https://custom.api.url"
        assert client.config.timeout == 60
