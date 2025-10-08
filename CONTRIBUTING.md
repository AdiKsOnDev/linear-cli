# Contributing to Linearator

Thank you for your interest in contributing to Linearator! This guide will help you get started with development and understand our workflow conventions.

## Table of Contents

- [Development Setup](#development-setup)
- [Commit Scopes](#commit-scopes)
- [Commit Message Format](#commit-message-format)
- [Commit Types](#commit-types)
- [Branch Naming](#branch-naming)
- [Making Changes](#making-changes)
- [Pull Request Guidelines](#pull-request-guidelines)
- [Code Quality Standards](#code-quality-standards)
- [Testing Requirements](#testing-requirements)
- [Review Process](#review-process)

## Development Setup

### Prerequisites

- Python 3.12 or higher
- Git
- pip and virtualenv

### Installation

1. Clone the repository:
```bash
git clone https://github.com/AdiKsOnDev/linearator.git
cd linearator
```

2. Create and activate a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install development dependencies:
```bash
make install-dev
```

4. Install pre-commit hooks:
```bash
make setup-hooks
```

### Development Commands

- `make test` - Run all tests
- `make test-cov` - Run tests with coverage report
- `make lint` - Run linting checks (ruff, mypy)
- `make format` - Format code with ruff
- `make security-check` - Run security checks (bandit)
- `make dev` - Format, lint, and test (quick workflow)
- `make ci` - Simulate CI/CD pipeline locally

## Commit Scopes

When making commits, use these predefined scopes in your conventional commit messages. Scopes represent specific areas of the codebase.

### API & Client
- `api` - Core Linear API client and GraphQL queries
- `auth` - Authentication, OAuth flow, and credential storage

### CLI Interface
- `cli` - Main CLI application and command infrastructure

### Commands
- `issue` - Issue management commands (create, list, update, delete)
- `project` - Project management and status updates
- `milestone` - Milestone operations and project-scoped milestones
- `team` - Team operations and member management
- `user` - User management and workload analysis
- `label` - Label creation and management
- `search` - Search functionality and filters
- `bulk` - Bulk operations (assignments, state updates, labels)
- `interactive` - Interactive mode and guided workflows

### Configuration & Utilities
- `config` - Configuration management and file handling
- `format` - Output formatters (table, JSON, YAML)

### Development & Infrastructure
- `test` - Test suite, fixtures, and test utilities
- `docs` - Documentation (README, CHANGELOG, guides)
- `ci` - CI/CD pipelines and GitHub Actions
- `build` - Build system, packaging, and distribution
- `deps` - Dependency updates and management

### Code Quality
- `security` - Security fixes and vulnerability patches
- `lint` - Linting configuration and fixes
- `types` - Type annotations and mypy compliance
- `perf` - Performance optimizations

## Commit Message Format

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>(<scope>): <subject>

[optional body]

[optional footer(s)]
```

### Format Rules

- **Subject line:** Maximum 50 characters
- **Subject style:** Imperative mood ("add" not "added" or "adds")
- **No capitalization:** Start with lowercase letter
- **No period:** Don't end subject with a period
- **Body:** Wrap at 72 characters (if included)
- **Separate:** Blank line between subject and body
- **Explain what and why:** Not how (code shows how)

### Breaking Changes

For breaking changes, add `!` after the type/scope:

```
feat(api)!: change authentication method signature

BREAKING CHANGE: The authenticate() method now requires
a context parameter as the first argument.
```

### Examples

**Good commits:**
```
feat(issue): add milestone assignment during creation
fix(auth): resolve keyring warning on systems without backend
docs(readme): add project structure section
test(milestone): add comprehensive unit test coverage
refactor(api): extract state resolution to helper function
perf(search): optimize GraphQL query for large result sets
```

**Bad commits:**
```
fixed bug                          # Missing type, scope, description
Added new feature.                 # Capitalized, has period
feat: Updates to the API client    # Capitalized, vague
fix(issue) Fixed the thing         # Missing colon, capitalized
```

## Commit Types

Use these types for all commits:

- `feat` - New feature for the user
- `fix` - Bug fix for the user
- `docs` - Documentation only changes
- `style` - Formatting, missing semicolons (no code change)
- `refactor` - Code change that neither fixes a bug nor adds a feature
- `perf` - Code change that improves performance
- `test` - Adding or correcting tests
- `build` - Changes to build system or dependencies
- `ci` - Changes to CI configuration and scripts
- `chore` - Other changes that don't modify src or test files
- `revert` - Reverts a previous commit

## Branch Naming

Follow this branch naming convention:

```
<type>/<short-description>
```

### Branch Types

- `feat/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation changes
- `refactor/` - Code refactoring
- `test/` - Test additions or modifications
- `chore/` - Maintenance tasks

### Branch Naming Rules

- Use lowercase letters only
- Separate words with hyphens
- Keep names short but descriptive
- Avoid special characters

### Examples

**Good branch names:**
```
feat/milestone-management
fix/auth-keyring-warnings
docs/contributing-guide
refactor/state-resolution
test/project-api-coverage
chore/update-dependencies
```

**Bad branch names:**
```
new-feature                  # Missing type prefix
feat/Add_New_Feature         # Uppercase, underscores
fix-bug                      # Missing slash separator
feat/implement-the-new-milestone-management-system-with-complete-testing  # Too long
```

## Making Changes

### 1. Create a Branch

```bash
git checkout -b feat/your-feature-name
```

### 2. Make Your Changes

- Write clean, readable code
- Follow existing code style
- Add tests for new functionality
- Update documentation as needed

### 3. Test Your Changes

```bash
# Run tests
make test

# Run linting
make lint

# Run security checks
make security-check

# Run full CI simulation
make ci
```

### 4. Commit Your Changes

```bash
# Stage changes
git add .

# Commit with conventional commit message
git commit -m "feat(scope): add new feature"
```

### 5. Push and Create PR

```bash
# Push to your fork
git push origin feat/your-feature-name

# Create pull request on GitHub
```

## Pull Request Guidelines

### PR Title Format

Use the same format as commit messages:

```
<type>(<scope>): <description>
```

### PR Description Template

```markdown
## Summary
Brief description of what this PR does

## Changes
- Change 1
- Change 2
- Change 3

## Testing
- [ ] All tests pass
- [ ] Added tests for new functionality
- [ ] Manually tested changes

## Documentation
- [ ] Updated README if needed
- [ ] Updated CHANGELOG
- [ ] Added/updated docstrings

## Checklist
- [ ] Code follows project style guidelines
- [ ] All tests pass locally
- [ ] No linting errors
- [ ] Security checks pass
- [ ] Breaking changes documented
```

### Before Submitting

Ensure your PR meets these requirements:

- ✓ All tests pass (`make test`)
- ✓ Code is properly formatted (`make format`)
- ✓ No linting errors (`make lint`)
- ✓ Security checks pass (`make security-check`)
- ✓ Test coverage is maintained or improved
- ✓ Documentation is updated
- ✓ CHANGELOG.md is updated (for notable changes)
- ✓ Commits follow conventional commit format
- ✓ Branch name follows naming convention

## Code Quality Standards

### Python Style

- **Formatter:** ruff (automatically applied)
- **Line Length:** 88 characters
- **Import Sorting:** Automated with ruff
- **Type Hints:** Required for all functions

### Type Safety

- **Type Checker:** mypy
- **Requirement:** 100% mypy compliance
- **Configuration:** Strict type checking enabled
- **Rules:**
  - All functions must have type annotations
  - No `Any` types unless absolutely necessary
  - Proper generic type parameters

### Security

- **Scanner:** bandit
- **Requirement:** Zero high/medium severity issues
- **Rules:**
  - No hardcoded secrets
  - Safe subprocess usage
  - Proper exception handling
  - Secure serialization (JSON, not pickle)

### Code Complexity

- Keep functions focused and simple
- Extract complex logic into helper functions
- Maximum cyclomatic complexity: 10
- Use meaningful variable names

## Testing Requirements

### Coverage Requirements

- **Minimum Coverage:** 80%
- **Target Coverage:** >90%
- **Requirement:** All new features must include tests

### Test Types

1. **Unit Tests:** Test individual functions and classes
2. **Integration Tests:** Test component interactions
3. **End-to-End Tests:** Test complete workflows

### Writing Tests

```python
def test_feature_description():
    """Test that feature behaves correctly under normal conditions."""
    # Arrange
    input_data = setup_test_data()

    # Act
    result = function_under_test(input_data)

    # Assert
    assert result == expected_output
```

### Test Commands

```bash
# Run all tests
make test

# Run with coverage
make test-cov

# Run unit tests only
make test-unit

# Run integration tests only
make test-integration
```

## Review Process

### What to Expect

1. **Automated Checks:** CI/CD pipeline runs tests, linting, and security checks
2. **Code Review:** Maintainers review code quality and design
3. **Feedback:** Reviewers may request changes or ask questions
4. **Iteration:** Make requested changes and push updates
5. **Approval:** Once approved, PR will be merged

### Review Criteria

Reviewers will check:

- ✓ Code quality and readability
- ✓ Test coverage and quality
- ✓ Documentation completeness
- ✓ Security considerations
- ✓ Performance implications
- ✓ Breaking change impact
- ✓ Consistency with existing code

### Getting Help

- **Issues:** [GitHub Issues](https://github.com/AdiKsOnDev/linearator/issues)
- **Discussions:** [GitHub Discussions](https://github.com/AdiKsOnDev/linearator/discussions)
- **Questions:** Open a discussion or comment on your PR

## Technology Stack

### Core Dependencies

- **CLI Framework:** Click
- **API Client:** GQL (GraphQL)
- **HTTP:** aiohttp, httpx
- **Authentication:** keyring, cryptography, PyJWT
- **Output:** rich (formatting)
- **Configuration:** python-dotenv, tomli/tomli-w

### Development Tools

- **Testing:** pytest, pytest-cov, pytest-asyncio, pytest-mock
- **Linting:** ruff, mypy
- **Security:** bandit, safety
- **Pre-commit:** pre-commit hooks

### Python Version

- **Minimum:** Python 3.12
- **Tested:** Python 3.12, 3.13

## Additional Resources

- [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
- [Semantic Versioning](https://semver.org/spec/v2.0.0.html)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Linear API Documentation](https://developers.linear.app/)

---

Thank you for contributing to Linearator! Your contributions help make this tool better for everyone.
