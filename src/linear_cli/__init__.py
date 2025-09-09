"""
Linearator - A comprehensive CLI tool for Linear issue management.

This package provides a command-line interface for interacting with Linear's API,
including issue management, team operations, and advanced search capabilities.
"""

__version__ = "1.0.5"
__author__ = "Linearator Team"
__email__ = "contact@linear-cli.dev"

from .api.client import LinearClient
from .config.manager import ConfigManager

__all__ = ["LinearClient", "ConfigManager"]
