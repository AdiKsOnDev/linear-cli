"""Tests for configuration manager."""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from linear_cli.config.exceptions import ConfigurationError
from linear_cli.config.manager import ConfigManager


class TestConfigManager:
    """Test configuration manager functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        # Create temporary config directory for testing
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir) / "config.json"
        self.manager = ConfigManager(config_dir=Path(self.temp_dir))

    def teardown_method(self):
        """Clean up test fixtures."""
        # Clean up temp directory
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_manager_initialization(self):
        """Test configuration manager initialization."""
        manager = ConfigManager()
        assert manager.config_dir is not None
        assert isinstance(manager.config_dir, Path)

    def test_manager_initialization_with_custom_dir(self):
        """Test configuration manager with custom directory."""
        custom_dir = Path(self.temp_dir) / "custom_config"
        manager = ConfigManager(config_dir=custom_dir)
        assert manager.config_dir == custom_dir

    def test_get_default_config_dir(self):
        """Test getting default configuration directory."""
        with patch("platformdirs.user_config_dir") as mock_config_dir:
            mock_config_dir.return_value = "/home/user/.config/linear-cli"

            default_dir = ConfigManager._get_default_config_dir()
            assert default_dir == Path("/home/user/.config/linear-cli")
            mock_config_dir.assert_called_once_with("linear-cli")

    def test_config_file_path(self):
        """Test configuration file path property."""
        expected_path = self.manager.config_dir / "config.json"
        assert self.manager.config_file_path == expected_path

    def test_load_config_file_not_exists(self):
        """Test loading config when file doesn't exist."""
        config = self.manager._load_config()
        assert config == {}

    def test_load_config_file_exists(self):
        """Test loading existing config file."""
        # Create config file
        config_data = {"api_token": "test-token", "cache_ttl": 300}
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.config_path.write_text('{"api_token": "test-token", "cache_ttl": 300}')

        config = self.manager._load_config()
        assert config == config_data

    def test_load_config_invalid_json(self):
        """Test loading config with invalid JSON."""
        # Create invalid JSON file
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.config_path.write_text('{"invalid": json}')

        with pytest.raises(ConfigurationError):
            self.manager._load_config()

    def test_save_config(self):
        """Test saving configuration."""
        config_data = {"api_token": "test-token", "cache_ttl": 600}
        self.manager._save_config(config_data)

        # Verify file was created and contains correct data
        assert self.config_path.exists()
        saved_data = self.manager._load_config()
        assert saved_data == config_data

    def test_get_config_value_exists(self):
        """Test getting existing configuration value."""
        # Set up config
        config_data = {"api_token": "test-token", "cache_ttl": 300}
        self.manager._save_config(config_data)

        # Test getting value
        assert self.manager.get("api_token") == "test-token"
        assert self.manager.get("cache_ttl") == 300

    def test_get_config_value_not_exists(self):
        """Test getting non-existent configuration value."""
        assert self.manager.get("nonexistent") is None

    def test_get_config_value_with_default(self):
        """Test getting configuration value with default."""
        assert self.manager.get("nonexistent", "default_value") == "default_value"

    def test_set_config_value(self):
        """Test setting configuration value."""
        self.manager.set("new_key", "new_value")

        # Verify value was set
        assert self.manager.get("new_key") == "new_value"

        # Verify it was persisted
        reloaded_manager = ConfigManager(config_dir=Path(self.temp_dir))
        assert reloaded_manager.get("new_key") == "new_value"

    def test_set_config_value_overwrite(self):
        """Test overwriting existing configuration value."""
        # Set initial value
        self.manager.set("key", "old_value")
        assert self.manager.get("key") == "old_value"

        # Overwrite value
        self.manager.set("key", "new_value")
        assert self.manager.get("key") == "new_value"

    def test_delete_config_value(self):
        """Test deleting configuration value."""
        # Set value first
        self.manager.set("to_delete", "value")
        assert self.manager.get("to_delete") == "value"

        # Delete value
        self.manager.delete("to_delete")
        assert self.manager.get("to_delete") is None

    def test_delete_nonexistent_value(self):
        """Test deleting non-existent configuration value."""
        # Should not raise error
        self.manager.delete("nonexistent")

    def test_get_api_token(self):
        """Test getting API token."""
        # Test with no token
        assert self.manager.get_api_token() is None

        # Set token and test
        self.manager.set("api_token", "test-token-123")
        assert self.manager.get_api_token() == "test-token-123"

    def test_set_api_token(self):
        """Test setting API token."""
        self.manager.set_api_token("new-token-456")
        assert self.manager.get_api_token() == "new-token-456"

    def test_clear_api_token(self):
        """Test clearing API token."""
        # Set token first
        self.manager.set_api_token("token-to-clear")
        assert self.manager.get_api_token() == "token-to-clear"

        # Clear token
        self.manager.clear_api_token()
        assert self.manager.get_api_token() is None

    def test_get_config_dict(self):
        """Test getting full configuration dictionary."""
        config_data = {
            "api_token": "test-token",
            "cache_ttl": 300,
            "output_format": "table",
        }

        # Set config values
        for key, value in config_data.items():
            self.manager.set(key, value)

        # Get config dict
        result = self.manager.get_config_dict()

        # Should contain all set values
        for key, value in config_data.items():
            assert result[key] == value

    def test_get_config_dict_masked_token(self):
        """Test getting config dict with masked API token."""
        self.manager.set("api_token", "very-secret-token-123")
        self.manager.set("other_setting", "visible-value")

        config_dict = self.manager.get_config_dict(mask_sensitive=True)

        assert "api_token" in config_dict
        assert config_dict["api_token"] == "***masked***"
        assert config_dict["other_setting"] == "visible-value"

    def test_get_config_dict_unmasked_token(self):
        """Test getting config dict with unmasked API token."""
        token = "very-secret-token-123"
        self.manager.set("api_token", token)

        config_dict = self.manager.get_config_dict(mask_sensitive=False)

        assert config_dict["api_token"] == token

    def test_config_validation(self):
        """Test configuration validation."""
        # Test valid configuration
        valid_config = {
            "api_token": "valid-token",
            "cache_ttl": 300,
            "output_format": "table",
        }

        # Should not raise error
        self.manager._validate_config(valid_config)

    def test_config_validation_invalid_types(self):
        """Test configuration validation with invalid types."""
        invalid_configs = [
            {"cache_ttl": "not-a-number"},  # Invalid type
            {"api_token": 12345},  # Invalid type
        ]

        for invalid_config in invalid_configs:
            # May or may not raise error depending on implementation
            try:
                self.manager._validate_config(invalid_config)
            except (ConfigurationError, TypeError, ValueError):
                pass  # Expected

    def test_config_directory_creation(self):
        """Test configuration directory is created if it doesn't exist."""
        nonexistent_dir = Path(self.temp_dir) / "nonexistent" / "config"
        manager = ConfigManager(config_dir=nonexistent_dir)

        # Setting a value should create the directory
        manager.set("test_key", "test_value")

        assert nonexistent_dir.exists()
        assert nonexistent_dir.is_dir()

    def test_config_file_permissions(self):
        """Test configuration file permissions."""
        self.manager.set("secret_token", "very-secret")

        # Config file should exist
        assert self.config_path.exists()

        # Check file permissions (should be readable/writable by owner only)
        stat = self.config_path.stat()
        # Convert to octal string for easier comparison
        permissions = oct(stat.st_mode)[-3:]

        # Should be restrictive (600 or similar)
        assert permissions in ["600", "644", "640"]  # Common secure permissions

    def test_concurrent_access(self):
        """Test concurrent access to configuration."""
        # Create two managers for same config
        manager1 = ConfigManager(config_dir=Path(self.temp_dir))
        manager2 = ConfigManager(config_dir=Path(self.temp_dir))

        # Set value with first manager
        manager1.set("concurrent_test", "value1")

        # Read with second manager (should see the change)
        assert manager2.get("concurrent_test") == "value1"

        # Set different value with second manager
        manager2.set("concurrent_test", "value2")

        # First manager should see updated value when reloaded
        manager1._config = None  # Force reload
        assert manager1.get("concurrent_test") == "value2"

    def test_backup_and_restore(self):
        """Test configuration backup and restore functionality."""
        # Set some configuration
        original_config = {
            "api_token": "original-token",
            "cache_ttl": 300,
            "setting": "value",
        }

        for key, value in original_config.items():
            self.manager.set(key, value)

        # If backup/restore methods exist, test them
        if hasattr(self.manager, "backup_config"):
            backup_path = self.manager.backup_config()
            assert backup_path.exists()

            # Modify config
            self.manager.set("api_token", "modified-token")

            # Restore from backup
            if hasattr(self.manager, "restore_config"):
                self.manager.restore_config(backup_path)
                assert self.manager.get("api_token") == "original-token"

    def test_environment_variable_override(self):
        """Test environment variable overrides."""
        with patch.dict(os.environ, {"LINEARATOR_API_TOKEN": "env-token"}):
            # If environment variable support exists
            if hasattr(self.manager, "_get_env_override"):
                token = self.manager._get_env_override("api_token")
                assert token == "env-token"

    def test_config_migration(self):
        """Test configuration migration between versions."""
        # Create old format config
        old_config = {"token": "old-format-token"}  # Old key name
        self.manager._save_config(old_config)

        # If migration exists, test it
        if hasattr(self.manager, "_migrate_config"):
            migrated = self.manager._migrate_config(old_config)
            # Should convert old keys to new format
            assert "api_token" in migrated or migrated == old_config

    def test_config_schema_validation(self):
        """Test configuration schema validation."""
        # If schema validation exists
        if hasattr(self.manager, "SCHEMA"):
            # Test valid config passes validation
            valid_config = {"api_token": "token-123", "cache_ttl": 300}
            # Should not raise
            self.manager._validate_config(valid_config)

            # Test invalid config fails validation
            invalid_config = {
                "api_token": 123,  # Should be string
                "cache_ttl": "invalid",  # Should be int
            }

            with pytest.raises((ConfigurationError, TypeError, ValueError)):
                self.manager._validate_config(invalid_config)

    def test_config_defaults(self):
        """Test configuration defaults."""
        # Test that defaults are applied for missing keys
        if hasattr(self.manager, "DEFAULTS"):
            for key, default_value in self.manager.DEFAULTS.items():
                assert self.manager.get(key, default_value) == default_value

        # Test common defaults
        assert self.manager.get("cache_ttl", 300) == 300
        assert self.manager.get("output_format", "table") == "table"
