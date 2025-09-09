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

## [Unreleased]

### Planned Features
- **Plugin System**: Extensible architecture for custom functionality
- **Integration Support**: Jira, Slack, and other tool integrations
- **Advanced Analytics**: Issue metrics and team performance insights
- **Template System**: Custom templates for recurring issue types
- **Workflow Automation**: Custom workflow rules and triggers

---

## Version History Summary

- **v1.0.4**: Major stability and testing improvements, authentication fixes
- **v1.0.0**: Initial production release with complete Linear CLI functionality
- **v0.x.x**: Development versions (pre-release)