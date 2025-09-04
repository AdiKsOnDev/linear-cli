Linearator Documentation
========================

**Linearator** is a comprehensive command-line interface for Linear issue management. It provides powerful tools for creating, managing, searching, and organizing issues with advanced filtering, bulk operations, and team collaboration features.

Features
--------

- **Complete Issue Management**: Full CRUD operations with rich filtering options
- **Advanced Search**: Full-text search with complex filters and query syntax  
- **Bulk Operations**: Efficient bulk updates, assignments, and labeling
- **Team Collaboration**: User management, workload analysis, and assignment suggestions
- **Interactive Mode**: Guided workflows for complex operations
- **Shell Integration**: Completion support for bash, zsh, and fish shells
- **Multiple Output Formats**: Table, JSON, and YAML output options
- **Professional Authentication**: OAuth and API key support with secure credential storage

Quick Start
-----------

Installation
~~~~~~~~~~~~

.. code-block:: bash

   pip install linear-cli

Authentication
~~~~~~~~~~~~~~

Before using Linearator, you need to authenticate with Linear:

.. code-block:: bash

   # OAuth authentication (recommended)
   linear-cli auth login

   # Or use API key
   export LINEAR_API_KEY="your-api-key"

Basic Usage
~~~~~~~~~~~

.. code-block:: bash

   # List issues
   linear-cli issue list

   # Create an issue
   linear-cli issue create "Fix authentication bug" --team ENG --priority 3

   # Search issues
   linear-cli search "authentication" --team ENG --priority 3

   # Bulk operations
   linear-cli bulk update-state -q "bug" --new-state "In Review"

   # User workload analysis
   linear-cli user workload --team ENG

   # Interactive mode for guided workflows
   linear-cli interactive

User Guide
----------

.. toctree::
   :maxdepth: 2
   :caption: User Guide

   installation
   authentication
   basic_usage
   advanced_features
   configuration
   examples

Command Reference
-----------------

.. toctree::
   :maxdepth: 2
   :caption: Commands

   commands/auth
   commands/issue
   commands/search
   commands/bulk
   commands/user
   commands/team
   commands/label
   commands/interactive
   commands/completion

API Reference
-------------

.. toctree::
   :maxdepth: 2
   :caption: API Reference

   api/cli
   api/client
   api/config
   api/auth

Developer Guide
---------------

.. toctree::
   :maxdepth: 2
   :caption: Development

   development/setup
   development/contributing
   development/architecture
   development/testing

Changelog
---------

.. toctree::
   :maxdepth: 1

   changelog

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`