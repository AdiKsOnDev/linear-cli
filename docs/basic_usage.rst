Basic Usage
===========

This guide covers the fundamental operations you can perform with Linearator. After authentication, you'll use these commands for day-to-day Linear workflow management.

Working with Issues
-------------------

Issues are the core entities in Linear. Linearator provides comprehensive issue management capabilities.

Creating Issues
~~~~~~~~~~~~~~~

.. code-block:: bash

   # Basic issue creation
   linear-cli issue create --title "Fix login bug"

   # Issue with full details
   linear-cli issue create \
     --title "Implement user dashboard" \
     --description "Create a dashboard showing user statistics and recent activity" \
     --team "Frontend" \
     --assignee "john@company.com" \
     --priority "High" \
     --label "feature,dashboard"

   # Interactive issue creation
   linear-cli issue create --interactive

Listing Issues
~~~~~~~~~~~~~~

.. code-block:: bash

   # List all your issues
   linear-cli issue list

   # Filter by status
   linear-cli issue list --status "In Progress,Todo"

   # Filter by assignee
   linear-cli issue list --assignee "john@company.com"

   # Filter by team
   linear-cli issue list --team "Backend"

   # Combine multiple filters
   linear-cli issue list --status "Todo" --team "Frontend" --priority "High"

   # List with specific output format
   linear-cli issue list --format json

Updating Issues
~~~~~~~~~~~~~~~

.. code-block:: bash

   # Update issue status
   linear-cli issue update ISS-123 --status "In Progress"

   # Assign issue to someone
   linear-cli issue update ISS-123 --assignee "jane@company.com"

   # Update multiple properties
   linear-cli issue update ISS-123 \
     --status "In Review" \
     --priority "Medium" \
     --add-label "reviewed"

   # Remove labels
   linear-cli issue update ISS-123 --remove-label "draft"

Viewing Issue Details
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # View full issue details
   linear-cli issue show ISS-123

   # View with comments
   linear-cli issue show ISS-123 --include-comments

   # JSON output for scripting
   linear-cli issue show ISS-123 --format json

Working with Teams
------------------

Team management is essential for organizing work across different groups.

Listing Teams
~~~~~~~~~~~~~

.. code-block:: bash

   # List all teams you have access to
   linear-cli team list

   # Get detailed team information
   linear-cli team info "Engineering"

Switching Team Context
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Set default team for future commands
   linear-cli team switch "Frontend"

   # Verify current team setting
   linear-cli config show | grep team

Working with Labels
-------------------

Labels help categorize and organize issues.

Managing Labels
~~~~~~~~~~~~~~~

.. code-block:: bash

   # List all available labels
   linear-cli label list

   # Create a new label
   linear-cli label create "refactor" \
     --description "Code refactoring tasks" \
     --color "#FF5722"

   # Apply labels to issues
   linear-cli label apply "bug" ISS-123 ISS-124

   # Remove labels from issues
   linear-cli label remove "draft" ISS-123

Basic Search
------------

Search helps you find issues quickly across your organization.

Text Search
~~~~~~~~~~~

.. code-block:: bash

   # Search by text content
   linear-cli search "authentication bug"

   # Search in specific team
   linear-cli search "dashboard" --team "Frontend"

   # Search with status filter
   linear-cli search "login" --status "Todo,In Progress"

Filter-Based Search
~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Find issues assigned to you
   linear-cli search --assignee "me"

   # Find high-priority issues
   linear-cli search --priority "High,Urgent"

   # Find recent issues
   linear-cli search --created-after "2024-01-01"

Output Formats
--------------

Linearator supports multiple output formats for different use cases.

Table Format (Default)
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   linear-cli issue list

Output::

   ID      Title                 Status       Assignee         Labels
   ISS-123 Fix authentication    In Progress  john@company.com bug, urgent
   ISS-124 User dashboard        Todo         jane@company.com feature
   ISS-125 Performance issue     Backlog      unassigned       performance

JSON Format
~~~~~~~~~~~

.. code-block:: bash

   linear-cli issue list --format json

.. code-block:: json

   [
     {
       "id": "ISS-123",
       "title": "Fix authentication",
       "status": "In Progress",
       "assignee": {
         "email": "john@company.com",
         "name": "John Doe"
       },
       "labels": ["bug", "urgent"],
       "priority": 1,
       "createdAt": "2024-01-15T10:30:00Z"
     }
   ]

Plain Format
~~~~~~~~~~~~

.. code-block:: bash

   linear-cli issue list --format plain

Output::

   ISS-123: Fix authentication (In Progress) - john@company.com
   ISS-124: User dashboard (Todo) - jane@company.com

Configuration
-------------

Configure Linearator for your workflow preferences.

View Current Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Show all configuration settings
   linear-cli config show

   # Show specific setting
   linear-cli config get default.team

Setting Configuration Values
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Set default team
   linear-cli config set default.team "Engineering"

   # Set default output format
   linear-cli config set output.format "json"

   # Set display preferences
   linear-cli config set display.colors true
   linear-cli config set display.progress_bars true

Common Workflows
----------------

Here are some typical workflows using Linearator.

Daily Standup Preparation
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   #!/bin/bash
   echo "=== Your active issues ==="
   linear-cli issue list --assignee me --status "In Progress,Todo"
   
   echo -e "\n=== Team urgent issues ==="
   linear-cli search --team "Engineering" --priority "Urgent"

Issue Triage
~~~~~~~~~~~~

.. code-block:: bash

   # Find unassigned issues
   linear-cli issue list --assignee unassigned --status Todo

   # Review issues without labels
   linear-cli search --no-labels --status Todo

   # Find old issues
   linear-cli search --created-before "30 days ago" --status Todo

Sprint Planning
~~~~~~~~~~~~~~~

.. code-block:: bash

   # List backlog for team
   linear-cli issue list --team "Frontend" --status Backlog

   # Find issues by priority
   linear-cli search --priority "High" --status "Todo,Backlog"

   # Check team workload
   linear-cli user workload --team "Frontend"

Tips and Best Practices
-----------------------

1. **Use aliases** for frequently used commands:

   .. code-block:: bash

      linear-cli config alias "my-issues" "issue list --assignee me"
      linear-cli config alias "urgent" "search --priority Urgent"

2. **Combine filters** to narrow down results:

   .. code-block:: bash

      linear-cli issue list --team Backend --status "In Progress" --assignee me

3. **Use JSON output** for scripting:

   .. code-block:: bash

      issues=$(linear-cli issue list --format json --status Todo)
      echo "$issues" | jq '.[] | select(.priority > 2)'

4. **Set up shell completion** for faster typing:

   .. code-block:: bash

      eval "$(_LINEARATOR_COMPLETE=bash_source linear-cli)"

5. **Use interactive mode** for complex operations:

   .. code-block:: bash

      linear-cli issue create --interactive