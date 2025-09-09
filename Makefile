# Makefile for Linearator development
# Provides common development tasks and workflows

.PHONY: help install install-dev clean test test-unit test-integration test-cov lint format check build dist upload docs serve-docs clean-docs pre-commit setup-hooks run debug

# Default Python interpreter
PYTHON ?= python3
PIP ?= pip3

# Project directories
SRC_DIR = src
TEST_DIR = tests
DOCS_DIR = docs

# Virtual environment detection
VENV_EXISTS := $(shell python -c "import sys; print('1' if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix) else '0')")

# Colors for terminal output
RED = \033[0;31m
GREEN = \033[0;32m
YELLOW = \033[1;33m
BLUE = \033[0;34m
BOLD = \033[1m
NC = \033[0m # No Color

help: ## Show this help message
	@echo "$(BOLD)Linearator Development Commands$(NC)"
	@echo ""
	@echo "$(BOLD)Setup Commands:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | grep -E '^(install|setup|clean)' | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(BLUE)%-15s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(BOLD)Development Commands:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | grep -E '^(test|lint|format|check|run|debug)' | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(BLUE)%-15s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(BOLD)Build & Distribution:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | grep -E '^(build|dist|upload|docs)' | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(BLUE)%-15s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@if [ "$(VENV_EXISTS)" = "0" ]; then \
		echo "$(YELLOW)⚠ Warning: No virtual environment detected$(NC)"; \
		echo "$(YELLOW)Consider running: python -m venv venv && source venv/bin/activate$(NC)"; \
		echo ""; \
	fi

# Installation Commands
install: ## Install package in development mode
	@echo "$(GREEN)Installing Linearator in development mode...$(NC)"
	$(PIP) install -e .

install-dev: ## Install with development dependencies
	@echo "$(GREEN)Installing Linearator with development dependencies...$(NC)"
	$(PIP) install -e ".[dev,test,docs]"

install-prod: ## Install for production use
	@echo "$(GREEN)Installing Linearator for production...$(NC)"
	$(PIP) install .

# Development Commands
run: ## Run the CLI application
	@echo "$(GREEN)Running Linearator...$(NC)"
	$(PYTHON) -m linearator

debug: ## Run with debug logging enabled
	@echo "$(GREEN)Running Linearator in debug mode...$(NC)"
	$(PYTHON) -m linearator --debug

# Testing Commands
test: ## Run all tests
	@echo "$(GREEN)Running all tests...$(NC)"
	$(PYTHON) -m pytest -k "not test_client" --tb=short --no-cov

test-unit: ## Run unit tests only
	@echo "$(GREEN)Running unit tests...$(NC)"
	$(PYTHON) -m pytest tests/unit/

test-integration: ## Run integration tests only
	@echo "$(GREEN)Running integration tests...$(NC)"
	$(PYTHON) -m pytest tests/integration/

test-cov: ## Run tests with coverage report
	@echo "$(GREEN)Running tests with coverage...$(NC)"
	$(PYTHON) -m pytest --cov=src/linearator --cov-report=html --cov-report=term-missing

test-watch: ## Run tests in watch mode
	@echo "$(GREEN)Running tests in watch mode (install pytest-watch first)...$(NC)"
	$(PYTHON) -m ptw

# Code Quality Commands
lint: ## Run linting checks
	@echo "$(GREEN)Running linting checks...$(NC)"
	$(PYTHON) -m ruff check $(SRC_DIR) $(TEST_DIR)
	$(PYTHON) -m mypy $(SRC_DIR)

format: ## Format code with black and ruff
	@echo "$(GREEN)Formatting code...$(NC)"
	$(PYTHON) -m black $(SRC_DIR) $(TEST_DIR)
	$(PYTHON) -m ruff check --fix $(SRC_DIR) $(TEST_DIR)

format-check: ## Check code formatting without making changes
	@echo "$(GREEN)Checking code formatting...$(NC)"
	$(PYTHON) -m black --check $(SRC_DIR) $(TEST_DIR)
	$(PYTHON) -m ruff check $(SRC_DIR) $(TEST_DIR)

check: format-check lint ## Run all code quality checks

# Pre-commit Commands
setup-hooks: ## Install pre-commit hooks
	@echo "$(GREEN)Installing pre-commit hooks...$(NC)"
	$(PYTHON) -m pre_commit install

pre-commit: ## Run pre-commit on all files
	@echo "$(GREEN)Running pre-commit on all files...$(NC)"
	$(PYTHON) -m pre_commit run --all-files

# Build Commands
build: clean ## Build distribution packages
	@echo "$(GREEN)Building distribution packages...$(NC)"
	$(PYTHON) -m build

dist: build ## Create distribution packages (alias for build)

upload-test: build ## Upload to Test PyPI
	@echo "$(GREEN)Uploading to Test PyPI...$(NC)"
	$(PYTHON) -m twine upload --repository testpypi dist/*

upload: build ## Upload to PyPI
	@echo "$(RED)Uploading to PyPI...$(NC)"
	@read -p "Are you sure you want to upload to PyPI? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		$(PYTHON) -m twine upload dist/*; \
	else \
		echo "Upload cancelled."; \
	fi

# Documentation Commands
docs: ## Build documentation
	@echo "$(GREEN)Building documentation...$(NC)"
	cd $(DOCS_DIR) && $(PYTHON) -m sphinx -b html . _build/html

docs-watch: ## Build and watch documentation
	@echo "$(GREEN)Building and watching documentation...$(NC)"
	cd $(DOCS_DIR) && $(PYTHON) -m sphinx_autobuild . _build/html

serve-docs: docs ## Serve documentation locally
	@echo "$(GREEN)Serving documentation at http://localhost:8000$(NC)"
	cd $(DOCS_DIR)/_build/html && $(PYTHON) -m http.server 8000

clean-docs: ## Clean documentation build files
	@echo "$(GREEN)Cleaning documentation build files...$(NC)"
	rm -rf $(DOCS_DIR)/_build

# Cleanup Commands
clean: ## Clean build artifacts and cache files
	@echo "$(GREEN)Cleaning build artifacts...$(NC)"
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	rm -rf htmlcov/
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete

clean-all: clean clean-docs ## Clean all generated files

# Development Setup
setup: install-dev setup-hooks ## Complete development setup
	@echo "$(GREEN)Development setup complete!$(NC)"
	@echo ""
	@echo "$(BOLD)Next steps:$(NC)"
	@echo "1. Run '$(BLUE)make test$(NC)' to verify installation"
	@echo "2. Run '$(BLUE)make run$(NC)' to start the CLI"
	@echo "3. Run '$(BLUE)make help$(NC)' to see all available commands"

# Quick development workflow
dev: format lint test ## Format, lint, and test (quick dev workflow)

# CI/CD simulation
ci: format-check lint test-cov ## Simulate CI/CD pipeline locally

# Release preparation
prepare-release: ## Prepare release with version bump (usage: make prepare-release VERSION=1.2.3)
	@if [ -z "$(VERSION)" ]; then \
		echo "$(RED)Error: VERSION is required. Usage: make prepare-release VERSION=1.2.3$(NC)"; \
		exit 1; \
	fi
	@echo "$(GREEN)Preparing release $(VERSION)...$(NC)"
	python scripts/prepare_release.py $(VERSION)

release-check: clean ci build docs ## Full release preparation check
	@echo "$(GREEN)Release check complete!$(NC)"
	@echo "Ready to upload with 'make upload-test' or 'make upload'"

# Environment info
info: ## Show development environment information
	@echo "$(BOLD)Environment Information:$(NC)"
	@echo "Python: $$($(PYTHON) --version)"
	@echo "Pip: $$($(PIP) --version)"
	@echo "Virtual Environment: $(if $(filter 1,$(VENV_EXISTS)),$(GREEN)Active$(NC),$(RED)Not Active$(NC))"
	@echo "Working Directory: $$(pwd)"
	@echo ""
	@echo "$(BOLD)Project Structure:$(NC)"
	@echo "Source: $(SRC_DIR)/"
	@echo "Tests: $(TEST_DIR)/"
	@echo "Docs: $(DOCS_DIR)/"

# Authentication testing (for development)
test-auth: ## Test authentication flow (requires config)
	@echo "$(GREEN)Testing authentication...$(NC)"
	$(PYTHON) -m linearator auth status

test-api: ## Test API connection
	@echo "$(GREEN)Testing API connection...$(NC)"
	$(PYTHON) -m linearator status

# Database/Config management
config-show: ## Show current configuration
	@echo "$(GREEN)Current configuration:$(NC)"
	$(PYTHON) -m linearator config show

config-reset: ## Reset configuration (with confirmation)
	@echo "$(YELLOW)This will reset all configuration to defaults.$(NC)"
	$(PYTHON) -m linearator config reset

# Utility targets
version: ## Show package version
	@$(PYTHON) -c "from src.linearator import __version__; print(__version__)"

deps-check: ## Check for outdated dependencies  
	$(PIP) list --outdated

deps-update: ## Update all dependencies (use with caution)
	$(PIP) install --upgrade pip setuptools wheel
	$(PIP) install --upgrade -e ".[dev,test,docs]"

# Platform-specific targets
windows-setup: ## Setup for Windows development
	@echo "$(GREEN)Setting up for Windows development...$(NC)"
	pip install -e ".[dev,test,docs]"
	pre-commit install

linux-setup: setup ## Setup for Linux development (alias for setup)

macos-setup: setup ## Setup for macOS development (alias for setup)

# Container support
docker-build: ## Build Docker development image
	@echo "$(GREEN)Building Docker development image...$(NC)"
	docker build -t linearator-dev -f Dockerfile.dev .

docker-run: ## Run in Docker container
	@echo "$(GREEN)Running in Docker container...$(NC)"
	docker run -it --rm -v $$(pwd):/app linearator-dev

docker-test: ## Run tests in Docker container
	@echo "$(GREEN)Running tests in Docker container...$(NC)"
	docker run --rm -v $$(pwd):/app linearator-dev make test

# Security and analysis
security-check: ## Run security checks
	@echo "$(GREEN)Running security checks...$(NC)"
	$(PYTHON) -m pip install safety bandit
	$(PYTHON) -m safety check
	$(PYTHON) -m bandit -r $(SRC_DIR)/

profile: ## Profile the application
	@echo "$(GREEN)Profiling application...$(NC)"
	$(PYTHON) -m cProfile -o profile.stats -m linearator --help
	$(PYTHON) -c "import pstats; p=pstats.Stats('profile.stats'); p.sort_stats('time').print_stats(20)"

# Git workflow helpers
git-clean: ## Clean git working directory
	git clean -fdx

git-reset: ## Reset to HEAD (destructive!)
	@echo "$(RED)This will reset all changes to HEAD. Are you sure?$(NC)"
	@read -p "Type 'yes' to continue: " -r; \
	if [[ $$REPLY == "yes" ]]; then git reset --hard HEAD; else echo "Cancelled."; fi