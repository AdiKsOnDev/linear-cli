"""
Linearator - A comprehensive CLI tool for Linear issue management.

This package provides a command-line interface for interacting with Linear's API,
including issue management, team operations, and advanced search capabilities.
"""

__version__ = "1.2.1"
__author__ = "Linearator Team"
__email__ = "adilalizada13@gmail.com"

from .api.client import LinearClient
from .config.manager import ConfigManager

__all__ = ["LinearClient", "ConfigManager"]
