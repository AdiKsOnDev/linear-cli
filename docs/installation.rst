Installation
============

System Requirements
-------------------

* Python 3.12 or higher
* Linear account with API access
* Internet connection for Linear API access

Installation Methods
--------------------

PyPI (Recommended)
~~~~~~~~~~~~~~~~~~

Install the latest stable version from PyPI:

.. code-block:: bash

   pip install linear-cli

Development Installation
~~~~~~~~~~~~~~~~~~~~~~~~

For development or to get the latest features:

.. code-block:: bash

   git clone https://github.com/linear-cli/linear-cli.git
   cd linear-cli
   pip install -e .

Verify Installation
~~~~~~~~~~~~~~~~~~~

Check that Linearator is installed correctly:

.. code-block:: bash

   linear-cli --version
   linear-cli status

Dependencies
------------

Linearator automatically installs the following dependencies:

* **click**: Command-line interface framework
* **rich**: Rich text and beautiful formatting
* **gql**: GraphQL client
* **aiohttp**: HTTP client for async operations
* **httpx**: Modern HTTP client
* **pydantic**: Data validation and settings management

Authentication Setup
--------------------

After installation, you'll need to authenticate with Linear. See the :doc:`authentication` guide for detailed instructions.

Shell Completion (Optional)
----------------------------

Enable shell completion for a better command-line experience:

.. code-block:: bash

   # For bash
   linear-cli completion install bash

   # For zsh  
   linear-cli completion install zsh

   # For fish
   linear-cli completion install fish

See the completion installation instructions displayed after running the command.

Troubleshooting
---------------

Permission Errors
~~~~~~~~~~~~~~~~~

If you encounter permission errors during installation:

.. code-block:: bash

   # Use user installation
   pip install --user linear-cli

   # Or use virtual environment (recommended)
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install linear-cli

Network Issues
~~~~~~~~~~~~~~

If installation fails due to network issues:

.. code-block:: bash

   # Use a different index
   pip install --index-url https://pypi.org/simple/ linear-cli

   # Or increase timeout
   pip install --timeout=60 linear-cli

Python Version Issues
~~~~~~~~~~~~~~~~~~~~~

Linearator requires Python 3.12 or higher. Check your Python version:

.. code-block:: bash

   python --version

If you have multiple Python versions, you may need to use:

.. code-block:: bash

   python3.12 -m pip install linear-cli

Updating
--------

To update to the latest version:

.. code-block:: bash

   pip install --upgrade linear-cli

To update to a specific version:

.. code-block:: bash

   pip install linear-cli==0.2.0

Uninstallation
--------------

To remove Linearator:

.. code-block:: bash

   pip uninstall linear-cli

This will remove the package but preserve your configuration files in ``~/.config/linear-cli/``.