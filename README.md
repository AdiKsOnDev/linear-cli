# Linearator

A comprehensive command-line interface for Linear issue management, enabling efficient project workflow automation and team collaboration through the Linear API.

## Overview

Linearator is a powerful CLI tool that streamlines Linear project management workflows by providing command-line access to all core Linear functionality. Built with Python and designed for developers, project managers, and teams who prefer terminal-based workflows or need to automate Linear operations.

## Key Features

### Core Issue Management
- **Full CRUD Operations**: Create, read, update, and delete Linear issues
- **Advanced Filtering**: Filter issues by status, assignee, labels, teams, and custom criteria
- **Bulk Operations**: Perform batch updates on multiple issues simultaneously
- **Status Management**: Update issue states, priorities, and assignments

### Team & Label Management
- **Team Operations**: List teams, switch contexts, manage team-specific configurations
- **Label Management**: Create, update, and apply labels to organize issues effectively
- **User Management**: View team members, workload distribution, and assignment suggestions

### Advanced Capabilities
- **Powerful Search**: Full-text search with advanced query syntax and saved searches
- **Interactive Mode**: Guided issue creation and management workflows
- **Multiple Output Formats**: JSON, table, and plain text formatting options
- **Shell Integration**: Command completion and aliases for efficient usage

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

### From Source

```bash
git clone https://github.com/linearator/linearator.git
cd linearator
pip install -e .
```

### Development Installation

```bash
git clone https://github.com/linearator/linearator.git
cd linearator
make install-dev
```

## Quick Start

### 1. Authentication

First, authenticate with Linear:

```bash
# OAuth flow (recommended)
linearator auth login

# Or use API key
linearator auth login --api-key YOUR_API_KEY
```

### 2. Basic Usage

```bash
# List your issues
linearator issue list

# Create a new issue
linearator issue create --title "Bug fix" --description "Fix login error" --team "ENG"

# Update issue status
linearator issue update ISS-123 --status "In Progress"

# Search issues
linearator search "login bug" --status "Todo" --assignee "john@company.com"
```

### 3. Team Operations

```bash
# List available teams
linearator team list

# Switch default team context
linearator team switch "Engineering"

# View team members
linearator user list --team "Engineering"
```

## Command Reference

### Issue Commands

```bash
# Create issues
linearator issue create --title "Title" --description "Description" --team "TEAM"
linearator issue create --interactive  # Guided creation

# List and filter issues
linearator issue list --status "In Progress" --assignee "user@email.com"
linearator issue list --label "bug,urgent" --team "Backend"

# Update issues
linearator issue update ISS-123 --status "Done" --assignee "user@email.com"
linearator issue update ISS-123 --add-label "critical" --priority "High"

# Delete issues
linearator issue delete ISS-123
```

### Bulk Operations

```bash
# Bulk status updates
linearator bulk update-status --status "In Progress" --filter "assignee:user@email.com"

# Bulk label management
linearator bulk add-label "refactor" --filter "team:Backend"

# Bulk assignment
linearator bulk assign "user@email.com" --filter "status:Todo,label:urgent"
```

### Search Operations

```bash
# Basic search
linearator search "authentication bug"

# Advanced search with filters
linearator search "login" --status "Todo,In Progress" --created-after "2024-01-01"

# Save and manage searches
linearator search save "urgent-bugs" "priority:urgent AND status:Todo"
linearator search run "urgent-bugs"
```

### Team & User Management

```bash
# Team operations
linearator team list
linearator team switch "Frontend"
linearator team info "Backend"

# User operations
linearator user list
linearator user workload --team "Engineering"
linearator user info "user@email.com"
```

### Label Management

```bash
# List labels
linearator label list

# Create labels
linearator label create "refactor" --description "Code refactoring tasks" --color "#FF5722"

# Apply labels to issues
linearator label apply "bug" ISS-123 ISS-124
```

### Configuration

```bash
# View configuration
linearator config show

# Set default values
linearator config set default.team "Engineering"
linearator config set output.format "table"

# Reset configuration
linearator config reset
```

## Configuration

Linearator supports configuration through multiple methods:

### Configuration File

Create `~/.linearator/config.toml`:

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
export LINEARATOR_DEFAULT_TEAM="Engineering"
export LINEARATOR_API_TOKEN="your_api_token"
export LINEARATOR_OUTPUT_FORMAT="json"
```

### Command Line Options

```bash
linearator --team "Engineering" --format json issue list
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
linearator issue list --format json
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

### Plain Text Format
```bash
linearator issue list --format plain
```

## Advanced Usage

### Interactive Mode

For complex operations, use interactive mode:

```bash
linearator issue create --interactive
linearator search --interactive
```

### Shell Completion

Enable shell completion for faster workflow:

```bash
# Bash
eval "$(_LINEARATOR_COMPLETE=bash_source linearator)"

# Zsh
eval "$(_LINEARATOR_COMPLETE=zsh_source linearator)"

# Fish
_LINEARATOR_COMPLETE=fish_source linearator | source
```

### Command Aliases

Set up aliases for frequently used commands:

```bash
linearator config alias "my-issues" "issue list --assignee me"
linearator config alias "urgent" "search 'priority:urgent'"
```

## Integration Examples

### CI/CD Integration

```yaml
# GitHub Actions example
- name: Create Linear issue for failed build
  run: |
    linearator issue create \
      --title "Build failed: ${{ github.ref }}" \
      --description "Build failure in ${{ github.repository }}" \
      --label "ci,bug" \
      --team "Engineering"
```

### Automation Scripts

```bash
#!/bin/bash
# Daily standup preparation
echo "Your issues for today:"
linearator issue list --assignee me --status "In Progress,Todo"

echo "Urgent team issues:"
linearator search "priority:urgent AND team:$TEAM"
```

## Development

### Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup

```bash
# Clone repository
git clone https://github.com/linearator/linearator.git
cd linearator

# Install development dependencies
make install-dev

# Run tests
make test

# Run linting
make lint

# Build documentation
make docs
```

### Running Tests

```bash
# Run all tests
make test

# Run specific test categories
make test-unit
make test-integration

# Run with coverage
make test-coverage
```

## Requirements

- Python 3.12 or higher
- Linear account with API access
- Internet connection for Linear API communication

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) file for details.

## Support

- **Documentation**: [linearator.readthedocs.io](https://linearator.readthedocs.io)
- **Issues**: [GitHub Issues](https://github.com/linearator/linearator/issues)
- **Discussions**: [GitHub Discussions](https://github.com/linearator/linearator/discussions)

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for detailed release notes and version history.