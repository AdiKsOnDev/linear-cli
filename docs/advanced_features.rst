Advanced Features
=================

This guide covers advanced Linearator features for power users and complex workflows. These features enable sophisticated automation and efficient bulk operations.

Bulk Operations
---------------

Bulk operations allow you to perform actions on multiple issues simultaneously, saving time and ensuring consistency.

Bulk Status Updates
~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Update all issues assigned to a user
   linearator bulk update-status \
     --status "In Review" \
     --filter "assignee:john@company.com AND status:In Progress"

   # Update all issues with specific label
   linearator bulk update-status \
     --status "Done" \
     --filter "label:bug AND status:In Review"

   # Bulk update with confirmation prompt
   linearator bulk update-status \
     --status "Backlog" \
     --filter "priority:Low AND created:<30d" \
     --confirm

Bulk Assignment
~~~~~~~~~~~~~~~

.. code-block:: bash

   # Assign all unassigned bugs to a user
   linearator bulk assign "jane@company.com" \
     --filter "assignee:unassigned AND label:bug"

   # Reassign issues from one user to another
   linearator bulk assign "newuser@company.com" \
     --filter "assignee:olduser@company.com"

   # Auto-assign based on team capacity
   linearator bulk auto-assign --team "Backend" --filter "status:Todo"

Bulk Labeling
~~~~~~~~~~~~~

.. code-block:: bash

   # Add label to all issues matching criteria
   linearator bulk add-label "needs-review" \
     --filter "status:In Progress AND assignee:me"

   # Remove outdated labels
   linearator bulk remove-label "sprint-1" \
     --filter "team:Frontend"

   # Replace labels
   linearator bulk replace-label "bug" "defect" \
     --filter "team:QA"

Advanced Search
---------------

Advanced search provides powerful query capabilities beyond basic text search.

Query Syntax
~~~~~~~~~~~~

Linearator supports a rich query language for complex searches:

.. code-block:: bash

   # Boolean operators
   linearator search "authentication AND (bug OR security)"

   # Field-specific searches
   linearator search "assignee:john@company.com AND priority:>2"

   # Date range searches
   linearator search "created:>2024-01-01 AND updated:<7d"

   # Team and label combinations
   linearator search "team:Backend AND label:bug AND NOT label:duplicate"

Search Filters
~~~~~~~~~~~~~~

.. code-block:: bash

   # Priority ranges
   linearator search --priority-min 2 --priority-max 4

   # Date filters
   linearator search --created-after "2024-01-01" --updated-before "7 days ago"

   # Complex assignee filters
   linearator search --assignee "john@company.com,jane@company.com" --no-assignee

   # State combinations
   linearator search --status "Todo,In Progress,In Review" --not-status "Done,Canceled"

Saved Searches
~~~~~~~~~~~~~~

.. code-block:: bash

   # Save frequently used searches
   linearator search save "my-urgent-issues" \
     "assignee:me AND priority:urgent AND status:Todo,In Progress"

   # Run saved searches
   linearator search run "my-urgent-issues"

   # List all saved searches
   linearator search list-saved

   # Update saved search
   linearator search update "my-urgent-issues" \
     "assignee:me AND priority:>=3 AND status:Todo,In Progress"

User Management
---------------

Advanced user management features help with team coordination and workload analysis.

Workload Analysis
~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Analyze team workload
   linearator user workload --team "Engineering"

   # Individual user workload
   linearator user workload --user "john@company.com"

   # Workload by priority
   linearator user workload --team "Frontend" --priority-breakdown

   # Historical workload trends
   linearator user workload --team "Backend" --since "30 days ago"

Assignment Suggestions
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Get assignment suggestions for new issues
   linearator user suggest-assignee \
     --issue-type "bug" \
     --team "Backend" \
     --skills "python,api"

   # Load balancing suggestions
   linearator user balance-workload --team "Frontend"

   # Suggest reviewers for issues
   linearator user suggest-reviewer ISS-123

User Analytics
~~~~~~~~~~~~~~

.. code-block:: bash

   # User performance metrics
   linearator user metrics "john@company.com" --since "30 days ago"

   # Team collaboration analysis
   linearator user collaboration --team "Engineering"

   # Issue completion rates
   linearator user completion-rate --team "QA" --period monthly

Interactive Mode
----------------

Interactive mode provides guided workflows for complex operations.

Interactive Issue Creation
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Start interactive issue creation
   linearator issue create --interactive

This will guide you through:

1. Issue title and description
2. Team selection
3. Assignee selection (with suggestions)
4. Priority setting
5. Label selection
6. Due date setting
7. Parent/child relationship setup

Interactive Search Builder
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Build complex searches interactively
   linearator search --interactive

Features:

- Step-by-step filter building
- Query syntax assistance
- Live preview of results
- Save search option

Interactive Bulk Operations
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Interactive bulk update
   linearator bulk --interactive

Includes:

- Filter building wizard
- Preview of affected issues
- Confirmation with impact analysis
- Rollback capability

Shell Integration
-----------------

Advanced shell integration features for power users.

Command Completion
~~~~~~~~~~~~~~~~~~

Enable advanced completion for your shell:

.. code-block:: bash

   # Bash (add to ~/.bashrc)
   eval "$(_LINEARATOR_COMPLETE=bash_source linearator)"

   # Zsh (add to ~/.zshrc)
   eval "$(_LINEARATOR_COMPLETE=zsh_source linearator)"

   # Fish (add to ~/.config/fish/config.fish)
   eval (env _LINEARATOR_COMPLETE=fish_source linearator)

Advanced completion features:

- Issue ID completion
- User email completion
- Team name completion
- Label completion
- Dynamic suggestions based on context

Command Aliases
~~~~~~~~~~~~~~~

Create custom aliases for complex commands:

.. code-block:: bash

   # Create aliases
   linearator config alias "bugs" "issue list --label bug --status Todo"
   linearator config alias "my-reviews" "issue list --assignee me --status 'In Review'"
   linearator config alias "standup" "issue list --assignee me --status 'In Progress,Todo'"

   # Use aliases
   linearator bugs
   linearator my-reviews
   linearator standup

Custom Commands
~~~~~~~~~~~~~~~

Create custom command combinations:

.. code-block:: bash

   # Create custom workflow scripts
   cat > ~/.linearator/scripts/daily-standup.sh << 'EOF'
   #!/bin/bash
   echo "=== Today's Focus ==="
   linearator issue list --assignee me --status "In Progress"
   
   echo -e "\n=== Ready for Review ==="
   linearator issue list --assignee me --status "In Review"
   
   echo -e "\n=== Up Next ==="
   linearator issue list --assignee me --status "Todo" --limit 3
   EOF

   chmod +x ~/.linearator/scripts/daily-standup.sh
   linearator config alias "standup" "!~/.linearator/scripts/daily-standup.sh"

Performance Optimization
------------------------

Features for optimizing performance with large datasets.

Caching
~~~~~~~

.. code-block:: bash

   # Enable response caching
   linearator config set cache.enabled true
   linearator config set cache.duration "5m"

   # Clear cache when needed
   linearator cache clear

   # View cache statistics
   linearator cache stats

Pagination
~~~~~~~~~~

.. code-block:: bash

   # Control result pagination
   linearator issue list --limit 50 --offset 0

   # Stream large result sets
   linearator issue list --stream --all-teams

   # Parallel processing
   linearator bulk update-status --parallel --batch-size 100

API Optimization
~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Configure API settings
   linearator config set api.timeout 30
   linearator config set api.retries 3
   linearator config set api.rate_limit 100

   # Use GraphQL fragments for efficiency
   linearator config set api.use_fragments true

Advanced Configuration
----------------------

Complex configuration scenarios and customization.

Multiple Profiles
~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Create profiles for different contexts
   linearator config profile create "work" --team "Engineering" --format "table"
   linearator config profile create "personal" --team "Personal" --format "json"

   # Switch between profiles
   linearator config profile use "work"

   # Profile-specific commands
   linearator --profile "personal" issue list

Environment-Specific Settings
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Development environment
   linearator config env create "dev" \
     --api-url "https://dev-api.linear.app/graphql" \
     --team "Development"

   # Production environment
   linearator config env create "prod" \
     --api-url "https://api.linear.app/graphql" \
     --team "Production"

Custom Output Formats
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Define custom output templates
   linearator config template create "brief" \
     --format "{{.id}}: {{.title}} ({{.status}})"

   # Use custom templates
   linearator issue list --template "brief"

Automation Examples
-------------------

Real-world automation scenarios using advanced features.

Daily Automation
~~~~~~~~~~~~~~~~

.. code-block:: bash

   #!/bin/bash
   # Daily cleanup and organization script

   # Close stale issues
   linearator bulk update-status --status "Canceled" \
     --filter "status:Todo AND updated:<30d AND assignee:unassigned"

   # Auto-assign urgent issues
   linearator bulk auto-assign --team "Support" \
     --filter "priority:urgent AND assignee:unassigned"

   # Generate daily report
   linearator user workload --team "Engineering" --format json > daily-workload.json

Sprint Management
~~~~~~~~~~~~~~~~~

.. code-block:: bash

   #!/bin/bash
   # Sprint planning automation

   # Move completed issues to Done
   linearator bulk update-status --status "Done" \
     --filter "status:'In Review' AND label:approved"

   # Identify sprint candidates
   linearator search "priority:>=3 AND status:Backlog AND estimate:<=8" \
     --format json > sprint-candidates.json

   # Balance workload for next sprint
   linearator user balance-workload --team "Development" \
     --target-capacity 40