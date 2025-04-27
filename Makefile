-include env.sh
export

.PHONY: help generate-lock-file sync-venv pre-commit-install pre-commit ruff run-tests run-tests-cov visualize-zones clean

cur-dir := $(shell pwd)
base-dir := $(shell basename $(cur-dir))

help: ## Display this help screen
	@grep -h -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

generate-lock-file: ## Generate a uv.lock file from pyproject.toml
	@uv lock

sync-venv: ## Sync local environment for Python development on pipelines
	@uv sync --all-groups

pre-commit-install: ## Install pre-commit hooks
	@uv run pre-commit install --install-hooks

pre-commit: ## Runs the pre-commit checks over entire repo
	@uv run pre-commit run --all-files --color=always

ruff: ## Runs ruff linting and formatting
	@if [ -n "$(path)" ]; then \
		uv run ruff check --fix $(path) && \
		uv run ruff format $(path); \
	else \
		uv run ruff check --fix && \
		uv run ruff format; \
	fi

# run: ## Run application
# 	@uv run -m src.main

# run-debug: ## Run application with debug mode enabled
# 	@uv run -m src.main -d

run-tests: ## Run tests
	@if [ -n "$(path)" ]; then \
		uv run coverage run -m pytest $(path); \
	else \
		uv run coverage run -m pytest; \
	fi

run-tests-cov: ## Run tests with coverage
	@uv run pytest -n auto --cov=src tests

visualize-zones: ## Visualize zones
	@uv run -m src.scripts.visualize_ztl_zones $(city)

clean: ## Remove generated files like __pycache__, .coverage, etc.
	@find . -type d -name "__pycache__" -exec rm -rf {} +
	@find . -type f -name "*.pyc" -delete
	@find . -type f -name "*.pyo" -delete
	@find . -type f -name "*.pyd" -delete
	@find . -type d -name "*.egg-info" -exec rm -rf {} +
	@find . -type d -name "*.egg" -exec rm -rf {} +
	@find . -type f -name ".coverage" -delete
	@find . -type d -name "htmlcov" -exec rm -rf {} +
	@find . -type d -name ".pytest_cache" -exec rm -rf {} +
	@find . -type d -name ".ruff_cache" -exec rm -rf {} +
	@rm -rf dist/ build/ .coverage
