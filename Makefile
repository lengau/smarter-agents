# Makefile for smarter-agents

PROJECT := smarter-agents
PYTHON_SOURCES := installer.py
YAML_SOURCES := collections.yaml .yamllint.yaml .coderabbit.yaml .github/workflows/*.yml
MD_SOURCES := README.md rules/*.md

.DEFAULT_GOAL := help

.PHONY: help
help: ## Show this help message
	@printf "\033[1m%-20s\033[0m %s\n" "Target" "Description"
	@printf "%-20s %s\n" "--------------------" "----------------------------------------"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

.PHONY: lint
lint: lint-yaml lint-md lint-python ## Run all repository linters

.PHONY: lint-yaml
lint-yaml: ## Check YAML files with yamlfmt and yamllint
	@echo "==> Running yamllint..."
	yamllint -c .yamllint.yaml .
	@echo "==> Running yamlfmt check..."
	yamlfmt -lint .

.PHONY: lint-md
lint-md: ## Check Markdown files with pymarkdownlnt
	@echo "==> Running pymarkdownlnt..."
	uv tool run pymarkdownlnt --config .pymarkdown.json scan $(MD_SOURCES)

.PHONY: lint-python
lint-python: ## Check Python files with ruff
	@echo "==> Running ruff check..."
	ruff check $(PYTHON_SOURCES)

.PHONY: format
format: format-yaml format-md format-python ## Format all files in the repository

.PHONY: format-yaml
format-yaml: ## Format YAML files with yamlfmt
	@echo "==> Formatting YAML with yamlfmt..."
	yamlfmt .

.PHONY: format-md
format-md: ## Format Markdown files with pymarkdownlnt
	@echo "==> Formatting Markdown with pymarkdownlnt..."
	uv tool run pymarkdownlnt --config .pymarkdown.json fix $(MD_SOURCES)

.PHONY: format-python
format-python: ## Format Python files with ruff
	@echo "==> Formatting Python with ruff..."
	ruff format $(PYTHON_SOURCES)
	ruff check --fix $(PYTHON_SOURCES)

.PHONY: test
test: ## Run tests
	@echo "==> Running tests..."
	python3 installer.py --help > /dev/null
	@echo "All tests passed."
