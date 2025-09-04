"""
Configuration-related exceptions.

Defines custom exceptions for configuration management errors.
"""


class ConfigurationError(Exception):
    """Base exception for configuration errors."""

    pass


class InvalidConfigError(ConfigurationError):
    """Raised when configuration is invalid."""

    pass


class ConfigFileError(ConfigurationError):
    """Raised when configuration file operations fail."""

    pass
