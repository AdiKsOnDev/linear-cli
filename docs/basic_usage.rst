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
   linearator issue create --title "Fix login bug"

   # Issue with full details
   linearator issue create \
     --title "Implement user dashboard" \
     --description "Create a dashboard showing user statistics and recent activity" \
     --team "Frontend" \
     --assignee "john@company.com" \
     --priority "High" \
     --label "feature,dashboard"

   # Interactive issue creation
   linearator issue create --interactive

Listing Issues
~~~~~~~~~~~~~~

.. code-block:: bash

   # List all your issues
   linearator issue list

   # Filter by status
   linearator issue list --status "In Progress,Todo"

   # Filter by assignee
   linearator issue list --assignee "john@company.com"

   # Filter by team
   linearator issue list --team "Backend"

   # Combine multiple filters
   linearator issue list --status "Todo" --team "Frontend" --priority "High"

   # List with specific output format
   linearator issue list --format json

Updating Issues
~~~~~~~~~~~~~~~

.. code-block:: bash

   # Update issue status
   linearator issue update ISS-123 --status "In Progress"

   # Assign issue to someone
   linearator issue update ISS-123 --assignee "jane@company.com"

   # Update multiple properties
   linearator issue update ISS-123 \
     --status "In Review" \
     --priority "Medium" \
     --add-label "reviewed"

   # Remove labels
   linearator issue update ISS-123 --remove-label "draft"

Viewing Issue Details
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # View full issue details
   linearator issue show ISS-123

   # View with comments
   linearator issue show ISS-123 --include-comments

   # JSON output for scripting
   linearator issue show ISS-123 --format json

Working with Teams
------------------

Team management is essential for organizing work across different groups.

Listing Teams
~~~~~~~~~~~~~

.. code-block:: bash

   # List all teams you have access to
   linearator team list

   # Get detailed team information
   linearator team info "Engineering"

Switching Team Context
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Set default team for future commands
   linearator team switch "Frontend"

   # Verify current team setting
   linearator config show | grep team

Working with Labels
-------------------

Labels help categorize and organize issues.

Managing Labels
~~~~~~~~~~~~~~~

.. code-block:: bash

   # List all available labels
   linearator label list

   # Create a new label
   linearator label create "refactor" \
     --description "Code refactoring tasks" \
     --color "#FF5722"

   # Apply labels to issues
   linearator label apply "bug" ISS-123 ISS-124

   # Remove labels from issues
   linearator label remove "draft" ISS-123

Basic Search
------------

Search helps you find issues quickly across your organization.

Text Search
~~~~~~~~~~~

.. code-block:: bash

   # Search by text content
   linearator search "authentication bug"

   # Search in specific team
   linearator search "dashboard" --team "Frontend"

   # Search with status filter
   linearator search "login" --status "Todo,In Progress"

Filter-Based Search
~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Find issues assigned to you
   linearator search --assignee "me"

   # Find high-priority issues
   linearator search --priority "High,Urgent"

   # Find recent issues
   linearator search --created-after "2024-01-01"

Output Formats
--------------

Linearator supports multiple output formats for different use cases.

Table Format (Default)
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   linearator issue list

Output::

   ID      Title                 Status       Assignee         Labels
   ISS-123 Fix authentication    In Progress  john@company.com bug, urgent
   ISS-124 User dashboard        Todo         jane@company.com feature
   ISS-125 Performance issue     Backlog      unassigned       performance

JSON Format
~~~~~~~~~~~

.. code-block:: bash

   linearator issue list --format json

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

   linearator issue list --format plain

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
   linearator config show

   # Show specific setting
   linearator config get default.team

Setting Configuration Values
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Set default team
   linearator config set default.team "Engineering"

   # Set default output format
   linearator config set output.format "json"

   # Set display preferences
   linearator config set display.colors true
   linearator config set display.progress_bars true

Common Workflows
----------------

Here are some typical workflows using Linearator.

Daily Standup Preparation
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   #!/bin/bash
   echo "=== Your active issues ==="
   linearator issue list --assignee me --status "In Progress,Todo"
   
   echo -e "\n=== Team urgent issues ==="
   linearator search --team "Engineering" --priority "Urgent"

Issue Triage
~~~~~~~~~~~~

.. code-block:: bash

   # Find unassigned issues
   linearator issue list --assignee unassigned --status Todo

   # Review issues without labels
   linearator search --no-labels --status Todo

   # Find old issues
   linearator search --created-before "30 days ago" --status Todo

Sprint Planning
~~~~~~~~~~~~~~~

.. code-block:: bash

   # List backlog for team
   linearator issue list --team "Frontend" --status Backlog

   # Find issues by priority
   linearator search --priority "High" --status "Todo,Backlog"

   # Check team workload
   linearator user workload --team "Frontend"

Tips and Best Practices
-----------------------

1. **Use aliases** for frequently used commands:

   .. code-block:: bash

      linearator config alias "my-issues" "issue list --assignee me"
      linearator config alias "urgent" "search --priority Urgent"

2. **Combine filters** to narrow down results:

   .. code-block:: bash

      linearator issue list --team Backend --status "In Progress" --assignee me

3. **Use JSON output** for scripting:

   .. code-block:: bash

      issues=$(linearator issue list --format json --status Todo)
      echo "$issues" | jq '.[] | select(.priority > 2)'

4. **Set up shell completion** for faster typing:

   .. code-block:: bash

      eval "$(_LINEARATOR_COMPLETE=bash_source linearator)"

5. **Use interactive mode** for complex operations:

   .. code-block:: bash

      linearator issue create --interactive