"""
Configuration management for Linearator.

Handles loading and saving configuration from multiple sources:
- Environment variables
- Configuration files (~/.linearator/config.toml)
- Command line arguments
"""

import logging
import os
import tomllib
from pathlib import Path
from typing import Any

import tomli_w
from dotenv import load_dotenv
from pydantic import BaseModel, Field, validator

logger = logging.getLogger(__name__)


class LinearConfig(BaseModel):
    """Linear API configuration model."""

    # Authentication
    access_token: str | None = Field(None, description="Linear API access token")
    client_id: str | None = Field(None, description="OAuth client ID")
    client_secret: str | None = Field(None, description="OAuth client secret")
    redirect_uri: str = Field(
        "http://localhost:8080/callback", description="OAuth redirect URI"
    )

    # API Configuration
    api_url: str = Field(
        "https://api.linear.app/graphql", description="Linear GraphQL API URL"
    )
    timeout: int = Field(30, description="API request timeout in seconds")
    max_retries: int = Field(3, description="Maximum number of API retries")

    # Default Settings
    default_team_id: str | None = Field(None, description="Default team ID")
    default_team_key: str | None = Field(None, description="Default team key")

    # Output Configuration
    output_format: str = Field(
        "table", description="Default output format (table, json, yaml)"
    )
    no_color: bool = Field(False, description="Disable colored output")
    verbose: bool = Field(False, description="Enable verbose logging")
    debug: bool = Field(False, description="Enable debug logging")

    # Cache Configuration
    cache_dir: Path | None = Field(None, description="Cache directory path")
    cache_ttl: int = Field(300, description="Cache TTL in seconds")

    @validator("cache_dir", pre=True, always=True)
    def set_cache_dir(cls, v: Any, values: dict[str, Any]) -> Path:
        if v is None:
            config_dir = Path.home() / ".linearator"
            return config_dir / "cache"
        return Path(v) if not isinstance(v, Path) else v

    @validator("timeout")
    def validate_timeout(cls, v: Any) -> int:
        if v <= 0:
            raise ValueError("Timeout must be positive")
        return int(v)

    @validator("max_retries")
    def validate_max_retries(cls, v: Any) -> int:
        if v < 0:
            raise ValueError("Max retries must be non-negative")
        return int(v)


class ConfigManager:
    """
    Manages configuration loading and saving for Linearator.

    Configuration precedence (highest to lowest):
    1. Command line arguments
    2. Environment variables
    3. User config file (~/.linearator/config.toml)
    4. Default values
    """

    def __init__(self, config_dir: Path | None = None):
        """Initialize the configuration manager."""
        self.config_dir = config_dir or Path.home() / ".linearator"
        self.config_file = self.config_dir / "config.toml"
        self._config: LinearConfig | None = None

        # Create config directory if it doesn't exist
        self.config_dir.mkdir(parents=True, exist_ok=True)

        # Load environment variables from .env file if present
        env_file = self.config_dir / ".env"
        if env_file.exists():
            load_dotenv(env_file)

    @property
    def config(self) -> LinearConfig:
        """Get the current configuration, loading it if not already loaded."""
        if self._config is None:
            self._config = self.load_config()
        return self._config

    def load_config(
        self, config_overrides: dict[str, Any] | None = None
    ) -> LinearConfig:
        """
        Load configuration from all sources.

        Args:
            config_overrides: Dictionary of configuration overrides (typically from CLI)

        Returns:
            LinearConfig: Loaded configuration
        """
        # Start with defaults
        config_data = {}

        # Load from config file
        if self.config_file.exists():
            try:
                with open(self.config_file, "rb") as f:
                    file_config = tomllib.load(f)
                config_data.update(file_config)
                logger.debug(f"Loaded config from {self.config_file}")
            except Exception as e:
                logger.warning(f"Failed to load config file {self.config_file}: {e}")

        # Load from environment variables
        env_config = self._load_from_env()
        config_data.update(env_config)

        # Apply overrides (typically from command line)
        if config_overrides:
            config_data.update(config_overrides)

        # Create and validate config
        try:
            config = LinearConfig(**config_data)
            self._config = config
            return config
        except Exception as e:
            logger.error(f"Configuration validation failed: {e}")
            raise ValueError(f"Invalid configuration: {e}") from e

    def _load_from_env(self) -> dict[str, Any]:
        """
        Load configuration from environment variables with type conversion.

        Maps LINEAR_* environment variables to configuration keys and performs
        appropriate type conversion for integers and booleans. Invalid values
        are logged and skipped to ensure configuration remains valid.

        Returns:
            Dictionary of configuration values from environment variables
        """
        env_mapping = {
            "LINEAR_ACCESS_TOKEN": "access_token",
            "LINEAR_CLIENT_ID": "client_id",
            "LINEAR_CLIENT_SECRET": "client_secret",
            "LINEAR_REDIRECT_URI": "redirect_uri",
            "LINEAR_API_URL": "api_url",
            "LINEAR_TIMEOUT": "timeout",
            "LINEAR_MAX_RETRIES": "max_retries",
            "LINEAR_DEFAULT_TEAM_ID": "default_team_id",
            "LINEAR_DEFAULT_TEAM_KEY": "default_team_key",
            "LINEAR_OUTPUT_FORMAT": "output_format",
            "LINEAR_NO_COLOR": "no_color",
            "LINEAR_VERBOSE": "verbose",
            "LINEAR_DEBUG": "debug",
            "LINEAR_CACHE_DIR": "cache_dir",
            "LINEAR_CACHE_TTL": "cache_ttl",
        }

        config: dict[str, Any] = {}
        for env_var, config_key in env_mapping.items():
            str_value = os.getenv(env_var)
            if str_value is not None:
                # Type conversion for specific fields
                if config_key in ("timeout", "max_retries", "cache_ttl"):
                    try:
                        int_value: int = int(str_value)
                        config[config_key] = int_value
                    except ValueError:
                        logger.warning(
                            f"Invalid integer value for {env_var}: {str_value}"
                        )
                        continue
                elif config_key in ("no_color", "verbose", "debug"):
                    bool_value: bool = str_value.lower() in ("true", "1", "yes", "on")
                    config[config_key] = bool_value
                elif config_key == "cache_dir":
                    path_value: Path = Path(str_value)
                    config[config_key] = path_value
                else:
                    config[config_key] = str_value

        return config

    def save_config(self, config: LinearConfig | None = None) -> None:
        """
        Save configuration to the config file.

        Args:
            config: Configuration to save. If None, saves current config.
        """
        if config is None:
            config = self.config

        # Convert config to dictionary, excluding None values
        config_dict = config.model_dump(exclude_none=True, exclude_unset=True)

        # Convert Path objects to strings for TOML serialization
        for key, value in config_dict.items():
            if isinstance(value, Path):
                config_dict[key] = str(value)

        try:
            with open(self.config_file, "wb") as f:
                tomli_w.dump(config_dict, f)
            logger.info(f"Configuration saved to {self.config_file}")
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            raise

    def update_config(self, **kwargs: Any) -> None:
        """
        Update configuration with new values and save.

        Args:
            **kwargs: Configuration fields to update
        """
        current_config = self.config.model_dump()
        current_config.update(kwargs)

        new_config = LinearConfig(**current_config)
        self._config = new_config
        self.save_config(new_config)

    def get_config_info(self) -> dict[str, Any]:
        """Get information about configuration sources and values."""
        return {
            "config_dir": str(self.config_dir),
            "config_file": str(self.config_file),
            "config_file_exists": self.config_file.exists(),
            "current_config": self.config.model_dump(exclude_none=True),
        }

    def reset_config(self) -> None:
        """Reset configuration to defaults and remove config file."""
        if self.config_file.exists():
            self.config_file.unlink()
            logger.info(f"Removed config file {self.config_file}")

        self._config = LinearConfig()
        logger.info("Configuration reset to defaults")
