"""
Unit tests for configuration module.

Tests the ConfigManager and LinearConfig classes.
"""

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from src.linear-cli.config.manager import ConfigManager, LinearConfig


class TestLinearConfig:
    """Test cases for LinearConfig class."""

    def test_default_config(self):
        """Test default configuration values."""
        config = LinearConfig()

        assert config.access_token is None
        assert config.client_id is None
        assert config.client_secret is None
        assert config.redirect_uri == "http://localhost:8080/callback"
        assert config.api_url == "https://api.linear.app/graphql"
        assert config.timeout == 30
        assert config.max_retries == 3
        assert config.output_format == "table"
        assert config.no_color is False
        assert config.verbose is False
        assert config.debug is False
        assert config.cache_ttl == 300

    def test_config_validation_timeout(self):
        """Test timeout validation."""
        with pytest.raises(ValueError, match="Timeout must be positive"):
            LinearConfig(timeout=0)

        with pytest.raises(ValueError, match="Timeout must be positive"):
            LinearConfig(timeout=-1)

    def test_config_validation_max_retries(self):
        """Test max retries validation."""
        with pytest.raises(ValueError, match="Max retries must be non-negative"):
            LinearConfig(max_retries=-1)

        # Zero retries should be allowed
        config = LinearConfig(max_retries=0)
        assert config.max_retries == 0

    def test_cache_dir_default(self):
        """Test cache directory default value."""
        config = LinearConfig()
        expected_dir = Path.home() / ".linear-cli" / "cache"
        assert config.cache_dir == expected_dir

    def test_cache_dir_custom(self):
        """Test custom cache directory."""
        custom_dir = Path("/tmp/custom_cache")
        config = LinearConfig(cache_dir=custom_dir)
        assert config.cache_dir == custom_dir


class TestConfigManager:
    """Test cases for ConfigManager class."""

    def test_init_default_dir(self):
        """Test initialization with default directory."""
        manager = ConfigManager()
        expected_dir = Path.home() / ".linear-cli"
        assert manager.config_dir == expected_dir
        assert manager.config_file == expected_dir / "config.toml"

    def test_init_custom_dir(self, temp_config_dir):
        """Test initialization with custom directory."""
        manager = ConfigManager(temp_config_dir)
        assert manager.config_dir == temp_config_dir
        assert manager.config_file == temp_config_dir / "config.toml"

    def test_load_config_defaults(self, config_manager):
        """Test loading configuration with defaults only."""
        config = config_manager.load_config()

        assert isinstance(config, LinearConfig)
        assert config.api_url == "https://api.linear.app/graphql"
        assert config.timeout == 30
        assert config.output_format == "table"

    def test_load_config_with_overrides(self, config_manager):
        """Test loading configuration with overrides."""
        overrides = {
            "timeout": 60,
            "verbose": True,
            "default_team_key": "TEST",
        }

        config = config_manager.load_config(overrides)

        assert config.timeout == 60
        assert config.verbose is True
        assert config.default_team_key == "TEST"

    def test_load_from_env(self, config_manager):
        """Test loading configuration from environment variables."""
        env_vars = {
            "LINEAR_ACCESS_TOKEN": "test_token",
            "LINEAR_CLIENT_ID": "test_client_id",
            "LINEAR_TIMEOUT": "45",
            "LINEAR_VERBOSE": "true",
            "LINEAR_DEBUG": "1",
            "LINEAR_NO_COLOR": "yes",
        }

        with patch.dict(os.environ, env_vars):
            config = config_manager.load_config()

        assert config.access_token == "test_token"
        assert config.client_id == "test_client_id"
        assert config.timeout == 45
        assert config.verbose is True
        assert config.debug is True
        assert config.no_color is True

    def test_load_from_env_invalid_int(self, config_manager):
        """Test loading invalid integer from environment."""
        with patch.dict(os.environ, {"LINEAR_TIMEOUT": "invalid"}):
            config = config_manager.load_config()
            # Should use default value when invalid
            assert config.timeout == 30

    def test_load_from_file(self, config_manager):
        """Test loading configuration from file."""
        config_data = """
        access_token = "file_token"
        client_id = "file_client_id"
        timeout = 60
        verbose = true
        default_team_key = "TEAM"
        """

        config_file = config_manager.config_file
        config_file.write_text(config_data)

        config = config_manager.load_config()

        assert config.access_token == "file_token"
        assert config.client_id == "file_client_id"
        assert config.timeout == 60
        assert config.verbose is True
        assert config.default_team_key == "TEAM"

    def test_load_from_file_invalid_toml(self, config_manager):
        """Test loading invalid TOML file."""
        config_file = config_manager.config_file
        config_file.write_text("invalid toml content [[[")

        # Should not raise exception, just use defaults
        config = config_manager.load_config()
        assert config.timeout == 30  # Default value

    def test_precedence_override_env_file(self, config_manager):
        """Test configuration precedence: overrides > env > file."""
        # File config
        config_data = "timeout = 50"
        config_file = config_manager.config_file
        config_file.write_text(config_data)

        # Environment config
        env_vars = {"LINEAR_TIMEOUT": "40"}

        # Override config
        overrides = {"timeout": 30}

        with patch.dict(os.environ, env_vars):
            config = config_manager.load_config(overrides)

        # Override should win
        assert config.timeout == 30

    def test_precedence_env_file(self, config_manager):
        """Test configuration precedence: env > file."""
        # File config
        config_data = "timeout = 50"
        config_file = config_manager.config_file
        config_file.write_text(config_data)

        # Environment config
        env_vars = {"LINEAR_TIMEOUT": "40"}

        with patch.dict(os.environ, env_vars):
            config = config_manager.load_config()

        # Environment should win
        assert config.timeout == 40

    def test_save_config(self, config_manager):
        """Test saving configuration to file."""
        config = LinearConfig(
            timeout=60,
            verbose=True,
            client_id="test_client",
        )

        config_manager.save_config(config)

        # Verify file was created and contains expected data
        assert config_manager.config_file.exists()

        # Load and verify
        loaded_config = config_manager.load_config()
        assert loaded_config.timeout == 60
        assert loaded_config.verbose is True
        assert loaded_config.client_id == "test_client"

    def test_save_config_current(self, config_manager):
        """Test saving current configuration."""
        # Load config and modify it
        config = config_manager.load_config({"timeout": 45, "verbose": True})
        config_manager._config = config

        # Save without parameters (should save current config)
        config_manager.save_config()

        # Load new manager and verify
        new_manager = ConfigManager(config_manager.config_dir)
        loaded_config = new_manager.load_config()
        assert loaded_config.timeout == 45
        assert loaded_config.verbose is True

    def test_update_config(self, config_manager):
        """Test updating configuration."""
        # Initial load
        config_manager.load_config()

        # Update configuration
        config_manager.update_config(
            timeout=120,
            verbose=True,
            default_team_key="NEW_TEAM",
        )

        # Verify changes
        assert config_manager.config.timeout == 120
        assert config_manager.config.verbose is True
        assert config_manager.config.default_team_key == "NEW_TEAM"

        # Verify file was saved
        assert config_manager.config_file.exists()

        # Load fresh and verify persistence
        new_manager = ConfigManager(config_manager.config_dir)
        loaded_config = new_manager.load_config()
        assert loaded_config.timeout == 120
        assert loaded_config.verbose is True
        assert loaded_config.default_team_key == "NEW_TEAM"

    def test_get_config_info(self, config_manager):
        """Test getting configuration information."""
        # Load config
        config_manager.load_config({"timeout": 60})

        info = config_manager.get_config_info()

        assert "config_dir" in info
        assert "config_file" in info
        assert "config_file_exists" in info
        assert "current_config" in info

        assert info["config_dir"] == str(config_manager.config_dir)
        assert info["config_file"] == str(config_manager.config_file)
        assert isinstance(info["current_config"], dict)
        assert info["current_config"]["timeout"] == 60

    def test_reset_config(self, config_manager):
        """Test resetting configuration."""
        # Create a config file
        config = LinearConfig(timeout=120, verbose=True)
        config_manager.save_config(config)
        assert config_manager.config_file.exists()

        # Load the config
        config_manager.load_config()
        assert config_manager.config.timeout == 120

        # Reset
        config_manager.reset_config()

        # Verify file is gone and config is reset
        assert not config_manager.config_file.exists()
        assert config_manager._config.timeout == 30  # Default value
        assert config_manager._config.verbose is False  # Default value

    def test_config_property_lazy_load(self, config_manager):
        """Test that config property loads configuration lazily."""
        # Config shouldn't be loaded initially
        assert config_manager._config is None

        # Accessing config property should load it
        config = config_manager.config
        assert config is not None
        assert isinstance(config, LinearConfig)
        assert config_manager._config is config

    def test_dotenv_loading(self, config_manager):
        """Test loading from .env file."""
        # Create .env file in config directory
        env_file = config_manager.config_dir / ".env"
        env_content = """
        LINEAR_ACCESS_TOKEN=env_file_token
        LINEAR_VERBOSE=true
        LINEAR_TIMEOUT=90
        """
        env_file.write_text(env_content)

        # Create new manager to trigger .env loading
        new_manager = ConfigManager(config_manager.config_dir)
        config = new_manager.load_config()

        # Values from .env should be loaded
        assert config.access_token == "env_file_token"
        assert config.verbose is True
        assert config.timeout == 90
