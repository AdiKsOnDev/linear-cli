# Linearator

A comprehensive command-line interface for Linear issue management, enabling efficient project workflow automation and team collaboration through the Linear API.

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Command Reference](#command-reference)
- [Configuration](#configuration)
- [Output Formats](#output-formats)
- [Advanced Usage](#advanced-usage)
- [Integration Examples](#integration-examples)
- [Project Structure](#project-structure)
- [Development](#development)
- [Requirements](#requirements)
- [License](#license)
- [Support](#support)
- [Changelog](#changelog)

## Overview

Linearator is a powerful CLI tool that streamlines Linear project management workflows by providing command-line access to core Linear functionality. Built with Python and designed for developers, project managers, and teams who prefer terminal-based workflows or need to automate Linear operations.

## Key Features

### Core Issue Management
- **Full CRUD Operations**: Create, read, update, and delete Linear issues
- **Advanced Filtering**: Filter issues by status, assignee, labels, teams, and custom criteria
- **Bulk Operations**: Perform batch updates on multiple issues simultaneously
- **Status Management**: Update issue states, priorities, and assignments

### Project Management
- **Project Operations**: List projects, view project details, and track project health
- **Project Updates**: Create and manage project status updates with health indicators
- **Project Timeline**: View project update history and track progress over time
- **Smart Lookup**: Reference projects by both ID and human-readable names

### Team & Label Management
- **Team Operations**: List teams, view team details, and manage team-specific configurations
- **Label Management**: Create, update, and apply labels to organize issues effectively
- **User Management**: View team members and workload analysis

### Advanced Capabilities
- **Powerful Search**: Full-text search with advanced filtering capabilities
- **Interactive Mode**: Guided issue creation and management workflows
- **Multiple Output Formats**: JSON, table, and YAML formatting options
- **Shell Integration**: Command completion for efficient usage

### Authentication & Security
- **OAuth Flow**: Secure authentication with Linear's OAuth system
- **API Key Support**: Alternative authentication method for automation
- **Credential Management**: Secure storage using system keyring
- **Token Refresh**: Automatic token renewal and session management

## Installation

### From PyPI (Recommended)

```bash
pip install linearator
```

### From AUR

```bash
paru -S linear-cli

# Or:
yay -S linear-cli
```

### From Source

```bash
git clone https://github.com/AdiKsOnDev/linearator.git
cd linearator
pip install -e .
```

### Development Installation

```bash
git clone https://github.com/AdiKsOnDev/linearator.git
cd linearator
make install-dev
```

## Quick Start

### 1. Authentication

First, authenticate with Linear:

```bash
# OAuth flow (recommended)
linear auth login

# Or use API key
linear auth login --api-key YOUR_API_KEY

# Or set environment variable
export LINEAR_API_KEY=YOUR_API_KEY
```

### 2. Basic Usage

```bash
# List your issues
linear issue list

# Create a new issue
linear issue create --title "Bug fix" --description "Fix login error" --team "ENG"

# Update issue status
linear issue update ISS-123 --status "In Progress"

# Search issues
linear search "login bug" --status "Todo" --assignee "john@company.com"
```

### 3. Team and Project Operations

```bash
# List available teams
linear team list

# View team details
linear team show "Engineering"

# List projects
linear project list

# View project details
linear project show "My Project"
```

## Command Reference

### Issue Commands

```bash
# Create issues
linear issue create --title "Title" --description "Description" --team "TEAM"

# List and filter issues
linear issue list --status "In Progress" --assignee "user@email.com"
linear issue list --labels "bug,urgent" --team "Backend"

# Update issues
linear issue update ISS-123 --status "Done" --assignee "user@email.com"
linear issue update ISS-123 --labels "critical" --priority "High"

# Show issue details
linear issue show ISS-123

# Delete issues
linear issue delete ISS-123
```

### Bulk Operations

```bash
# Bulk status updates
linear bulk update-state --status "In Progress" --filter "assignee:user@email.com"

# Bulk label management
linear bulk label --add "refactor" --filter "team:Backend"

# Bulk assignment
linear bulk assign "user@email.com" --filter "status:Todo"
```

### Search Operations

```bash
# Basic search
linear search "authentication bug"

# Advanced search with filters
linear search "login" --state "Todo" --priority 3
linear search "bug" --labels "urgent" --assignee "user@email.com"

# Advanced search with date filtering
linear search-advanced issues "api bug" --team "Backend" --limit 50
```

### Team & User Management

```bash
# Team operations
linear team list
linear team show "Backend"

# User operations
linear user list
linear user show "user@email.com"
linear user workload
```

### Project Management

```bash
# List all projects
linear project list

# View project details
linear project show "My Project"

# Create project status update
linear project update "My Project" "Made good progress this week" --health onTrack

# View project update history
linear project updates "My Project"
```

### Label Management

```bash
# List labels
linear label list

# Create labels
linear label create "refactor" --description "Code refactoring tasks" --color "#FF5722"

# Update labels
linear label update "bug" --description "Updated description" --color "#FF0000"

# Delete labels
linear label delete "old-label"
```

### Configuration

```bash
# View configuration
linear config show

# Set configuration values
linear config set default_team "Engineering"
linear config set output_format "table"

# Edit configuration in editor
linear config edit

# Reset configuration
linear config reset

# Unset configuration values
linear config unset default_team
```

## Configuration

Linear CLI supports configuration through multiple methods:

### Configuration File

Create `~/.linear-cli/config.toml`:

```toml
[default]
team = "Engineering"
output_format = "table"

[api]
timeout = 30
retries = 3

[display]
colors = true
progress_bars = true
```

### Environment Variables

```bash
export LINEAR_API_KEY="your_api_token"
export LINEARATOR_DEFAULT_TEAM="Engineering"
export LINEARATOR_OUTPUT_FORMAT="json"
```

### Command Line Options

```bash
linear --team "Engineering" --format json issue list
```

## Output Formats

### Table Format (Default)
```
ID      Title              Status        Assignee      Labels
ISS-123 Fix authentication In Progress   john@co.com   bug, urgent
ISS-124 Add user profiles  Todo          jane@co.com   feature
```

### JSON Format
```bash
linear issue list --format json
```

```json
[
  {
    "id": "ISS-123",
    "title": "Fix authentication",
    "status": "In Progress",
    "assignee": "john@company.com",
    "labels": ["bug", "urgent"],
    "createdAt": "2024-01-15T10:30:00Z"
  }
]
```

### YAML Format
```bash
linear issue list --format yaml
```

## Advanced Usage

### Interactive Mode

Start interactive mode for guided workflows:

```bash
linear interactive
```

### Shell Completion

Enable shell completion for faster workflow:

```bash
# Bash
eval "$(_LINEARATOR_COMPLETE=bash_source linear)"

# Zsh  
eval "$(_LINEARATOR_COMPLETE=zsh_source linear)"

# Fish
_LINEARATOR_COMPLETE=fish_source linear | source
```

## Integration Examples

### CI/CD Integration

```yaml
# GitHub Actions example
- name: Create Linear issue for failed build
  run: |
    linear issue create \
      --title "Build failed: ${{ github.ref }}" \
      --description "Build failure in ${{ github.repository }}" \
      --labels "ci,bug" \
      --team "Engineering"
```

### Automation Scripts

```bash
#!/bin/bash
# Daily standup preparation
echo "Your issues for today:"
linear issue list --assignee me --state "In Progress"

echo "Urgent issues:"
linear search "bug" --priority 4 --state "Todo"
```

## Project Structure

```
linearator/
├── src/
│   └── linear_cli/
│       ├── api/                  # Linear API integration
│       │   ├── auth/             # Authentication (OAuth, API keys)
│       │   ├── client/           # GraphQL client implementation
│       │   └── queries.py        # GraphQL query definitions
│       ├── cli/                  # CLI application
│       │   ├── commands/         # Command implementations
│       │   │   ├── issue.py      # Issue management commands
│       │   │   ├── project.py    # Project management commands
│       │   │   ├── team.py       # Team operations
│       │   │   ├── user.py       # User management
│       │   │   ├── label.py      # Label operations
│       │   │   ├── search.py     # Search functionality
│       │   │   ├── bulk.py       # Bulk operations
│       │   │   ├── auth.py       # Authentication commands
│       │   │   ├── config.py     # Configuration management
│       │   │   └── interactive.py # Interactive mode
│       │   ├── app.py            # Main CLI application
│       │   └── formatters.py     # Output formatting (table, JSON, YAML)
│       ├── config/               # Configuration management
│       │   ├── manager.py        # Config file handling
│       │   └── exceptions.py     # Config-related exceptions
│       ├── utils/                # Utility functions
│       └── constants.py          # Application constants
├── tests/                        # Test suite
│   ├── unit/                     # Unit tests
│   └── integration/              # Integration tests
├── docs/                         # Documentation
├── scripts/                      # Utility scripts
├── .github/                      # GitHub workflows and templates
│   └── workflows/                # CI/CD pipelines
├── pyproject.toml                # Project configuration and dependencies
├── Makefile                      # Development commands
├── README.md                     # Project overview
├── CONTRIBUTING.md               # Contribution guidelines
├── CHANGELOG.md                  # Version history
└── LICENSE                       # MIT License
```

### Key Components

- **API Layer**: GraphQL client with comprehensive Linear API integration
- **CLI Commands**: Modular command structure for all Linear operations
- **Authentication**: OAuth and API key support with secure credential storage
- **Output Formatters**: Flexible output in table, JSON, and YAML formats
- **Configuration**: Multi-source config (files, env vars, CLI options)
- **Testing**: Comprehensive test coverage with unit and integration tests

## Development

### Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup

```bash
# Clone repository
git clone https://github.com/AdiKsOnDev/linearator.git
cd linearator

# Install development dependencies
make install-dev

# Run tests
make test

# Run linting and formatting
make lint
make format

# Run security checks
make security-check
```

### Running Tests

```bash
# Run all tests
make test

# Run tests with coverage
make test-coverage

# Run linting checks
make lint

# Check code formatting
make format-check
```

## Requirements

- Python 3.12 or higher
- Linear account with API access
- Internet connection for Linear API communication

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) file for details.

## Support

- **Issues**: [GitHub Issues](https://github.com/AdiKsOnDev/linearator/issues)
- **Discussions**: [GitHub Discussions](https://github.com/AdiKsOnDev/linearator/discussions)

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for detailed release notes and version history.
