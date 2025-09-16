# Changelog

All notable changes to Linear CLI will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2024-09-04

### Added
- **Complete CLI Framework**: Full-featured command-line interface for Linear issue management
- **Authentication System**: OAuth and API key authentication with secure credential storage
- **Issue Management**: Full CRUD operations with advanced filtering and status management
- **Search Capabilities**: Powerful full-text search with query syntax and saved searches
- **Bulk Operations**: Efficient batch updates, assignments, and label management
- **Team Management**: Team switching, member listing, and workload analysis
- **Label System**: Create, apply, and manage labels for issue organization
- **User Management**: User workload analysis, assignment suggestions, and collaboration tools
- **Interactive Mode**: Guided workflows for complex operations
- **Multiple Output Formats**: Table, JSON, and plain text formatting options
- **Configuration System**: Flexible configuration via files, environment variables, and CLI options
- **Shell Integration**: Command completion for Bash, Zsh, and Fish shells
- **Professional Documentation**: Complete user guide, API reference, and tutorials
- **Performance Optimizations**: Response caching, async operations, and connection pooling
- **Comprehensive Testing**: >90% test coverage with unit and integration tests

### Technical Features
- **GraphQL Client**: Efficient Linear API communication with query optimization
- **Error Handling**: Robust error handling with informative messages
- **Progress Indicators**: Visual feedback for long-running operations
- **Rate Limiting**: Automatic rate limit handling and retry logic
- **Cross-Platform**: Support for Linux, macOS, and Windows
- **Type Safety**: Full type annotations with mypy validation
- **Code Quality**: Automated linting, formatting, and security scanning

### Documentation
- **User Guide**: Complete documentation with examples and tutorials
- **API Reference**: Auto-generated API documentation
- **Configuration Guide**: Comprehensive configuration options and examples
- **Advanced Features**: Detailed guides for power users and automation
- **Development Guide**: Setup instructions for contributors

### Infrastructure
- **CI/CD Pipeline**: Automated testing, linting, and release processes
- **PyPI Distribution**: Professional package distribution with proper metadata
- **Development Tools**: Make targets, pre-commit hooks, and development environment
- **Quality Assurance**: Comprehensive test suite with coverage reporting

## [1.0.4] - 2024-12-08

### Fixed
- **Authentication**: Fixed automatic API key detection from `LINEAR_API_KEY` environment variable
- **GraphQL Issues**: Resolved orderBy parameter format for issue listing and search operations  
- **Search Functionality**: Fixed search results parsing and display formatting
- **Team Management**: Corrected member count display using proper GraphQL field structure
- **Test Suite**: Completely overhauled test suite for reliability and speed
  - Fixed package name references throughout test files
  - Resolved formatter edge cases and null value handling  
  - Eliminated hanging tests that caused timeouts
  - Achieved 100% passing test rate (277 tests pass in ~1.4 seconds)
- **CI/CD Pipeline**: Updated GitHub Actions to latest versions
  - Upgraded deprecated `actions/upload-artifact` from v3 to v4
  - Updated all core actions to latest stable versions
  - Fixed codecov integration with proper token handling

### Improved
- **Error Handling**: Enhanced error messages and graceful failure modes
- **Performance**: Significantly improved test execution time (4000% faster)
- **Code Quality**: Fixed formatting issues and improved type safety
- **Development Experience**: Streamlined `make test` command for reliable testing

### Technical Enhancements
- **Bearer Token Fix**: Corrected Linear API authentication format (removed invalid Bearer prefix)
- **UTC Time Handling**: Fixed timezone conversion in datetime formatting
- **Label Processing**: Enhanced label formatting to handle both GraphQL and list formats
- **Package Structure**: Resolved import path issues from project rename

## [1.0.5] - 2024-12-09

### Changed
- **Package Name**: Renamed PyPI package from `linear-cli` to `linearator` to avoid naming conflicts
- **Publishing**: Added automated PyPI publishing workflow with GitHub trusted publishing
- **Release Process**: Implemented automatic package building, testing, and publishing on release

### Added
- **Automated Publishing**: Complete CI/CD pipeline for PyPI package distribution
- **Multi-Python Testing**: Automated testing on Python 3.12 and 3.13 during publishing
- **Security**: GitHub trusted publishing integration (no API tokens required)
- **Release Artifacts**: Automatic upload of wheel and source distributions to GitHub releases

### Technical
- **Workflow**: Added `.github/workflows/publish-pypi.yml` for automated publishing
- **Environment**: Optional PyPI environment configuration for additional security
- **Testing**: Pre-publish testing ensures package integrity before distribution

## [1.0.6] - 2024-12-09

### Security
- **Vulnerability Fixes**: Resolved all security issues identified by Bandit security scanner
- **Safe Serialization**: Replaced pickle with JSON for cache files to prevent deserialization attacks
- **Input Validation**: Added validation for subprocess calls in config editor functionality
- **Authentication**: Fixed test authentication state to prevent environment variable interference

### Fixed
- **Test Suite**: All tests now pass reliably (277/277 passing)
- **Version Display**: Fixed CLI version command to show correct version number
- **Environment Variables**: Improved handling of LINEAR_API_KEY environment variable in tests
- **Cache Security**: Enhanced performance cache with safer JSON-based persistence

### Technical
- **Bandit Compliance**: Addressed all medium and high severity security warnings
- **Test Isolation**: Improved test fixtures to prevent environment variable conflicts
- **Code Quality**: Enhanced error handling with proper logging instead of silent failures
- **Editor Validation**: Added whitelist validation for safe text editors in config command

## [1.0.7] - 2025-09-09

### Fixed
- **Keyring Warnings**: Eliminated annoying keyring backend warnings that appeared on every CLI command
- **Credential Storage**: Improved error handling for systems without keyring backends
- **User Experience**: Clean CLI startup without unnecessary warning messages

### Changed
- **Logging Levels**: Reduced keyring-related messages from ERROR/WARNING to DEBUG level
- **Fallback Behavior**: More graceful fallback to PBKDF2 encryption when keyring unavailable

### Technical
- **Proactive Detection**: Added keyring availability check before attempting operations
- **Silent Fallback**: Automatic fallback to secure PBKDF2 without user-visible warnings
- **Improved Error Handling**: Better separation of expected vs unexpected credential storage errors

## [1.0.8] - 2025-09-09

### Fixed
- **AUR Package Dependencies**: Fixed PKGBUILD to properly install Python dependencies from PyPI
- **Dependency Resolution**: Updated package installation to use `pip install` for complete dependency management
- **Import Errors**: Resolved "No module named 'gql'" and similar import errors in AUR package

### Changed
- **Release Script**: Updated to handle PKGBUILD and .SRCINFO files in project root
- **AUR Workflow**: Simplified file structure for easier AUR package maintenance
- **Package Installation**: Changed from `python-installer` to `pip install` for better dependency handling

### Technical
- **PKGBUILD**: Now installs directly from PyPI with full dependency resolution
- **File Paths**: Moved AUR packaging files to project root for easier access
- **Release Automation**: Enhanced release script to automatically update AUR package metadata

## [1.1.0] - 2025-09-09

### Added
- **🎯 Project Management**: Complete project management functionality
  - `linear project list` - List all projects with state, health, progress, and lead information
  - `linear project show <name-or-id>` - Show detailed project information (supports both names and IDs)
  - `linear project update <name-or-id> <message> [--health <status>]` - Create project status updates
  - `linear project updates <name-or-id>` - List project update history with user attribution
- **📊 Enhanced Issue Display**: Issues now show associated project names in detailed views
- **🔍 Smart Project Lookup**: Projects can be referenced by both ID and name for better usability
- **📈 Project Health Tracking**: Support for onTrack, atRisk, offTrack, and complete health statuses
- **📝 Project Updates**: Full project status update system with health indicators and timeline
- **🎨 Rich Formatting**: Project information displayed with tables, colors, and markdown support

### Enhanced
- **GraphQL API Coverage**: Added comprehensive project queries and mutations
- **Client Methods**: New project-related API client methods with error handling
- **Output Formatters**: Dynamic project formatting methods with multiple output formats (table, JSON, YAML)
- **Command Structure**: Integrated project commands into main CLI application

### Fixed  
- **Code Formatting**: Fixed all ruff and black formatting issues for consistent code style
- **Exception Handling**: Improved exception handling with proper `raise ... from err` patterns
- **Import Optimization**: Removed unused imports and variables identified by linting tools
- **Try/Except Pattern**: Enhanced exception handling with proper logging instead of silent pass

### Security
- **🛡️ Security Compliance**: Complete bandit security scan compliance
  - Fixed try/except/pass patterns with proper logging
  - Added `.bandit` configuration file to manage security exceptions  
  - Updated subprocess usage with documented security justifications
  - Enhanced exception handling throughout codebase
- **🔧 CI/CD Security**: Updated GitHub workflows and Makefile to use bandit configuration
- **✅ Pipeline Ready**: All security checks now pass in CI/CD pipeline

### Technical
- **Project API Integration**: Full GraphQL schema coverage for Linear project operations
- **Smart Name Resolution**: Project lookup works with both UUIDs and human-readable names
- **Error Recovery**: Graceful fallback from ID lookup to name-based search
- **Test Markers**: Added `@pytest.mark.keyring` for CI test filtering
- **CI Reliability**: Excluded keyring-dependent tests from GitHub Actions (7 tests) while maintaining local development testing
- **Configuration Management**: Centralized bandit security configuration with documented exceptions

## [1.2.0] - 2025-09-15

### Added
- **🎯 Project Assignment to Issues**: Issues can now be assigned to projects during creation and updates
  - `linear issue create "Bug fix" --project "Q4 Sprint"` - Assign project by name during creation
  - `linear issue update ENG-123 --project "Backend Refactor"` - Update existing issue with project assignment
  - Supports both project names and IDs with comprehensive validation
  - Smart project lookup with user-friendly error messages
- **📋 Enhanced Label Management**: Multi-team label discovery and filtering capabilities
  - `linear label list --team ENG --team QA` - Check labels across multiple specific teams
  - `linear label list --all-teams` - View labels from all accessible teams at once
  - Backward compatibility maintained with existing single-team filtering
  - Team context displayed for better label organization
- **🏗️ Project Creation**: Complete project lifecycle management functionality
  - `linear project create "New Project" --description "Project desc" --team ENG` - Create projects with full configuration
  - Team assignment, lead assignment, and state management support
  - Comprehensive validation and user-friendly error handling
  - Integration with existing project management commands

### Enhanced
- **GraphQL API Coverage**: Extended with new project creation mutations and enhanced label queries
- **CLI Consistency**: All new functionality follows existing command patterns and output formatting
- **Error Handling**: Robust validation with graceful degradation and helpful user feedback
- **Type Safety**: Complete mypy compliance with proper type annotations throughout

### Fixed
- **Code Quality**: Resolved 17 mypy type safety errors in formatters module
  - Fixed missing generic type parameters and return type annotations
  - Restructured dynamic method assignment patterns for better maintainability
  - Achieved 100% mypy compliance across all modified files
- **Style Issues**: Applied comprehensive code formatting with ruff
  - Eliminated all trailing whitespace and formatting inconsistencies
  - Consistent code style across the entire codebase

### Documentation
- **Comprehensive WHY Comments**: Added business logic explanations for complex operations
  - Explained team info enrichment logic for multi-team label context
  - Documented project lookup strategy reasoning and performance optimizations
  - Added clear documentation for GraphQL query purposes and efficiency considerations
- **Complete Docstring Coverage**: 100% docstring coverage for all new functionality
- **CLI Help Integration**: All new commands properly documented with examples and usage patterns

## [1.2.1] - 2025-09-16

### Improved
- **Enhanced CLI Help Text**: Improved clarity and examples for all new functionality
  - Clarified that `--project` parameter supports both project names and IDs
  - Enhanced multi-team label filtering help text with better descriptions
  - Added comprehensive usage examples showcasing project assignment features
  - Improved project creation help with clearer team association descriptions
  - Added examples demonstrating combined parameter usage

### Documentation
- **CLI Help Integration**: All new commands now have comprehensive help text with practical examples
- **User Experience**: Better guidance for users discovering new project assignment and label management features

## [Unreleased]

### Planned Features
- **Plugin System**: Extensible architecture for custom functionality
- **Integration Support**: Jira, Slack, and other tool integrations
- **Advanced Analytics**: Issue metrics and team performance insights
- **Template System**: Custom templates for recurring issue types
- **Workflow Automation**: Custom workflow rules and triggers
- **AUR**: Possibility to install this package through AUR

---

## Version History Summary

- **v1.0.4**: Major stability and testing improvements, authentication fixes
- **v1.0.0**: Initial production release with complete Linear CLI functionality
- **v0.x.x**: Development versions (pre-release)
