Authentication
==============

Linearator supports multiple authentication methods to connect with Linear's API. This guide covers all authentication options and credential management.

OAuth Authentication (Recommended)
-----------------------------------

OAuth provides the most secure authentication method with automatic token refresh.

Initial Setup
~~~~~~~~~~~~~

.. code-block:: bash

   # Start OAuth flow
   linear-cli auth login

   # Follow the browser prompts to authorize Linearator
   # Tokens will be securely stored in your system keyring

Checking Authentication Status
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Check current authentication status
   linear-cli auth status

   # View stored credentials (without exposing secrets)
   linear-cli auth info

API Key Authentication
----------------------

For automation or environments where OAuth isn't suitable, you can use API keys.

Using API Keys
~~~~~~~~~~~~~~

.. code-block:: bash

   # Set API key via command line
   linear-cli auth login --api-key YOUR_API_KEY

   # Or set via environment variable
   export LINEAR_API_KEY="your-api-key-here"
   linear-cli auth login

Generating API Keys
~~~~~~~~~~~~~~~~~~~

1. Go to Linear Settings > API
2. Click "Create new key"
3. Give it a descriptive name (e.g., "Linearator CLI")
4. Copy the generated key immediately (it won't be shown again)

Environment Variables
---------------------

Linearator recognizes several environment variables for authentication:

.. code-block:: bash

   # Primary API token
   export LINEAR_API_KEY="your-api-key"

   # OAuth tokens (managed automatically)
   export LINEAR_ACCESS_TOKEN="oauth-access-token"
   export LINEAR_REFRESH_TOKEN="oauth-refresh-token"

   # API endpoint (rarely needed to change)
   export LINEAR_API_URL="https://api.linear.app/graphql"

Credential Storage
------------------

Linearator uses your system's secure keyring to store credentials:

- **macOS**: Keychain
- **Linux**: Secret Service (GNOME Keyring, KWallet)
- **Windows**: Windows Credential Locker

Manual Credential Management
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Remove stored credentials
   linear-cli auth logout

   # Force refresh of OAuth tokens
   linear-cli auth refresh

   # Clear all stored authentication data
   linear-cli auth reset

Configuration File Authentication
---------------------------------

You can also store authentication in your configuration file (less secure):

.. code-block:: toml

   # ~/.linear-cli/config.toml
   [auth]
   api_key = "your-api-key"
   # Note: OAuth tokens should not be stored in config files

Team-Specific Authentication
----------------------------

For organizations with multiple Linear workspaces:

.. code-block:: bash

   # Authenticate with specific workspace
   linear-cli auth login --workspace "company-workspace"

   # Switch between authenticated workspaces
   linear-cli auth switch-workspace "other-workspace"

   # List available workspaces
   linear-cli auth list-workspaces

Troubleshooting Authentication
------------------------------

Common Issues
~~~~~~~~~~~~~

**Token Expired**

.. code-block:: bash

   # Refresh OAuth tokens
   linear-cli auth refresh

   # Or re-authenticate
   linear-cli auth login

**Invalid API Key**

.. code-block:: bash

   # Verify your API key
   linear-cli auth status --verbose

   # Generate a new API key from Linear Settings

**Keyring Access Issues**

.. code-block:: bash

   # Use environment variables instead
   export LINEAR_API_KEY="your-key"

   # Or store in config file
   linear-cli config set auth.api_key "your-key"

Permission Scopes
-----------------

Different authentication methods provide different permission levels:

API Key Permissions
~~~~~~~~~~~~~~~~~~~

- Read/write access to issues
- Team and user information
- Label management
- Search capabilities

OAuth Permissions
~~~~~~~~~~~~~~~~~

- All API key permissions
- Secure token refresh
- Workspace-level permissions
- Enhanced rate limiting

Security Best Practices
-----------------------

1. **Use OAuth when possible** - Most secure with automatic token refresh
2. **Rotate API keys regularly** - Generate new keys periodically
3. **Don't share credentials** - Each user should have their own authentication
4. **Use environment variables in CI/CD** - Never commit credentials to repositories
5. **Monitor API usage** - Check Linear's API usage dashboard regularly

Example: CI/CD Setup
~~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   # GitHub Actions example
   name: Linear Integration
   on: [push]
   
   jobs:
     create-issue:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v3
         - name: Setup Python
           uses: actions/setup-python@v4
           with:
             python-version: '3.12'
         - name: Install Linearator
           run: pip install linear-cli
         - name: Create issue on failure
           if: failure()
           run: |
             linear-cli issue create \
               --title "Build failed: ${{ github.sha }}" \
               --description "Build failed on ${{ github.ref }}" \
               --team "Engineering"
           env:
             LINEAR_API_KEY: ${{ secrets.LINEAR_API_KEY }}