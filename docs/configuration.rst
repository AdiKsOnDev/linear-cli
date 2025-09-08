Configuration
=============

Linearator provides flexible configuration options through configuration files, environment variables, and command-line options. This guide covers all configuration methods and available settings.

Configuration Methods
----------------------

Linearator follows a standard configuration precedence:

1. **Command-line options** (highest priority)
2. **Environment variables**
3. **Configuration files**
4. **Default values** (lowest priority)

Configuration Files
-------------------

Linearator uses TOML format for configuration files.

Default Configuration File
~~~~~~~~~~~~~~~~~~~~~~~~~~

The main configuration file is located at:

- **Linux/macOS**: ``~/.linear/config.toml``
- **Windows**: ``%APPDATA%\Linearator\config.toml``

Example configuration file:

.. code-block:: toml

   [default]
   team = "Engineering"
   output_format = "table"
   editor = "code"

   [api]
   timeout = 30
   retries = 3
   rate_limit = 100

   [auth]
   # API key can be stored here (less secure than keyring)
   # api_key = "your-api-key"

   [display]
   colors = true
   progress_bars = true
   table_style = "grid"

   [cache]
   enabled = true
   duration = "5m"
   max_size = "100MB"

   [aliases]
   bugs = "issue list --label bug --status Todo"
   my-issues = "issue list --assignee me"
   urgent = "search --priority urgent"

Project-Specific Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can also create project-specific configuration files:

.. code-block:: bash

   # Create project config in current directory
   linear config init --local

This creates ``.linear.toml`` in the current directory with project-specific settings.

Configuration Sections
-----------------------

Default Settings
~~~~~~~~~~~~~~~~

.. code-block:: toml

   [default]
   # Default team for operations
   team = "Engineering"
   
   # Default output format: table, json, plain, yaml
   output_format = "table"
   
   # Default text editor for issue descriptions
   editor = "vim"
   
   # Default assignee for new issues: me, unassigned, or email
   assignee = "me"
   
   # Default priority for new issues (1-4)
   priority = 2

API Configuration
~~~~~~~~~~~~~~~~~

.. code-block:: toml

   [api]
   # API endpoint (rarely needs to change)
   url = "https://api.linear.app/graphql"
   
   # Request timeout in seconds
   timeout = 30
   
   # Number of retry attempts for failed requests
   retries = 3
   
   # Rate limit (requests per minute)
   rate_limit = 100
   
   # Enable request/response logging for debugging
   debug = false
   
   # User agent string
   user_agent = "Linearator/1.0"

Authentication Settings
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: toml

   [auth]
   # API key (less secure than keyring storage)
   # api_key = "your-api-key-here"
   
   # OAuth settings
   client_id = "your-oauth-client-id"
   redirect_uri = "http://localhost:8080/callback"
   
   # Token refresh settings
   auto_refresh = true
   refresh_threshold = "5m"

Display Configuration
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: toml

   [display]
   # Enable colored output
   colors = true
   
   # Show progress bars for long operations
   progress_bars = true
   
   # Table display style: simple, grid, fancy_grid, outline
   table_style = "grid"
   
   # Maximum width for table columns
   max_column_width = 50
   
   # Date format for timestamps
   date_format = "%Y-%m-%d %H:%M"
   
   # Truncate long text in tables
   truncate_text = true

Caching Settings
~~~~~~~~~~~~~~~~

.. code-block:: toml

   [cache]
   # Enable response caching
   enabled = true
   
   # Cache duration (e.g., "5m", "1h", "30s")
   duration = "5m"
   
   # Maximum cache size
   max_size = "100MB"
   
   # Cache directory
   directory = "~/.linear/cache"
   
   # Cache compression
   compress = true

Search Configuration
~~~~~~~~~~~~~~~~~~~~

.. code-block:: toml

   [search]
   # Default search limit
   default_limit = 50
   
   # Enable fuzzy search
   fuzzy = true
   
   # Search result highlighting
   highlight = true
   
   # Save search history
   save_history = true
   
   # Maximum saved searches
   max_saved = 100

Bulk Operation Settings
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: toml

   [bulk]
   # Batch size for bulk operations
   batch_size = 50
   
   # Enable parallel processing
   parallel = true
   
   # Maximum parallel workers
   max_workers = 4
   
   # Confirmation prompt for bulk operations
   confirm_operations = true
   
   # Dry run by default
   dry_run = false

Environment Variables
---------------------

All configuration options can be set via environment variables using the format ``LINEARATOR_SECTION_OPTION``:

Authentication
~~~~~~~~~~~~~~

.. code-block:: bash

   # Primary API authentication
   export LINEARATOR_API_KEY="your-api-key"
   export LINEARATOR_AUTH_API_KEY="your-api-key"  # Alternative format

   # OAuth tokens (managed automatically)
   export LINEARATOR_AUTH_ACCESS_TOKEN="access-token"
   export LINEARATOR_AUTH_REFRESH_TOKEN="refresh-token"

Default Settings
~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Default team
   export LINEARATOR_DEFAULT_TEAM="Engineering"
   
   # Output format
   export LINEARATOR_DEFAULT_OUTPUT_FORMAT="json"
   
   # Default assignee
   export LINEARATOR_DEFAULT_ASSIGNEE="john@company.com"

API Settings
~~~~~~~~~~~~

.. code-block:: bash

   # API configuration
   export LINEARATOR_API_URL="https://api.linear.app/graphql"
   export LINEARATOR_API_TIMEOUT="30"
   export LINEARATOR_API_RETRIES="3"
   export LINEARATOR_API_DEBUG="true"

Display Settings
~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Display preferences
   export LINEARATOR_DISPLAY_COLORS="true"
   export LINEARATOR_DISPLAY_PROGRESS_BARS="false"
   export LINEARATOR_DISPLAY_TABLE_STYLE="simple"

Command-Line Configuration
--------------------------

Use ``linear config`` command to manage configuration:

Viewing Configuration
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Show all configuration
   linear config show

   # Show specific section
   linear config show auth

   # Get specific value
   linear config get default.team

Setting Configuration
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Set configuration values
   linear config set default.team "Frontend"
   linear config set api.timeout 60
   linear config set display.colors false

   # Set nested values
   linear config set auth.auto_refresh true

Removing Configuration
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Remove specific setting
   linear config unset default.team

   # Reset section to defaults
   linear config reset auth

   # Reset entire configuration
   linear config reset --all

Configuration Validation
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Validate current configuration
   linear config validate

   # Check for configuration issues
   linear config doctor

Aliases
-------

Create command aliases for frequently used operations:

Creating Aliases
~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Create simple aliases
   linear config alias "bugs" "issue list --label bug"
   linear config alias "my-todo" "issue list --assignee me --status Todo"

   # Complex aliases with multiple commands
   linear config alias "standup" "issue list --assignee me --status 'In Progress,Todo'"

Using Aliases
~~~~~~~~~~~~~

.. code-block:: bash

   # Use aliases like regular commands
   linear bugs
   linear my-todo
   linear standup

Managing Aliases
~~~~~~~~~~~~~~~~

.. code-block:: bash

   # List all aliases
   linear config alias list

   # Show alias definition
   linear config alias show "bugs"

   # Remove alias
   linear config alias remove "bugs"

Profiles
--------

Profiles allow you to maintain different configuration sets for different contexts.

Creating Profiles
~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Create work profile
   linear config profile create "work" \
     --team "Engineering" \
     --format "table" \
     --colors true

   # Create personal profile
   linear config profile create "personal" \
     --team "Personal Projects" \
     --format "json" \
     --colors false

Using Profiles
~~~~~~~~~~~~~~

.. code-block:: bash

   # Switch to a profile
   linear config profile use "work"

   # Run command with specific profile
   linear --profile "personal" issue list

   # Show current profile
   linear config profile current

Managing Profiles
~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # List all profiles
   linear config profile list

   # Show profile settings
   linear config profile show "work"

   # Delete profile
   linear config profile delete "personal"

Advanced Configuration
----------------------

Custom Output Templates
~~~~~~~~~~~~~~~~~~~~~~~

Define custom output formats:

.. code-block:: toml

   [templates]
   brief = "{{.id}}: {{.title}} ({{.status}})"
   detailed = """
   ID: {{.id}}
   Title: {{.title}}
   Status: {{.status}}
   Assignee: {{.assignee.name}}
   Created: {{.created_at | date}}
   """

.. code-block:: bash

   # Use custom template
   linear issue list --template brief

Plugin Configuration
~~~~~~~~~~~~~~~~~~~~

Configure plugins and extensions:

.. code-block:: toml

   [plugins]
   enabled = ["jira-sync", "slack-notifications"]
   
   [plugins.jira-sync]
   url = "https://company.atlassian.net"
   username = "integration@company.com"
   
   [plugins.slack-notifications]
   webhook_url = "https://hooks.slack.com/services/..."
   channel = "#engineering"

Troubleshooting Configuration
-----------------------------

Common Issues
~~~~~~~~~~~~~

**Configuration Not Loading**

.. code-block:: bash

   # Check configuration file location
   linear config file-path

   # Validate configuration syntax
   linear config validate

   # Show effective configuration (after merging all sources)
   linear config show --effective

**Environment Variable Issues**

.. code-block:: bash

   # List environment variables affecting Linearator
   linear config env-vars

   # Show configuration sources and precedence
   linear config debug

**Permission Issues**

.. code-block:: bash

   # Check configuration directory permissions
   ls -la ~/.linear/

   # Reset configuration directory
   linear config init --reset

Migration and Backup
--------------------

Backup Configuration
~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Export current configuration
   linear config export > my-linear-config.toml

   # Export specific profile
   linear config export --profile work > work-config.toml

Restore Configuration
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Import configuration
   linear config import my-linear-config.toml

   # Import as new profile
   linear config import work-config.toml --profile work

Migration Between Versions
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Migrate configuration to new format
   linear config migrate

   # Show migration status
   linear config migration-status