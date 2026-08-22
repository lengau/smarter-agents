# Makefile for smarter-agents

PROJECT := smarter-agents
PYTHON_SOURCES := installer.py skills/context-checkpoint/scripts/checkpoint.py tests/test_checkpoint.py
YAML_SOURCES := collections.yaml .yamllint.yaml .coderabbit.yaml .pre-commit-config.yaml .github/workflows/*.yaml
JSON_SOURCES := .pymarkdown.json .github/renovate.json skills/context-checkpoint/schemas/checkpoint.schema.json skills/context-checkpoint/templates/checkpoint.template.json
MD_SOURCES := README.md rules/*.md skills/context-checkpoint/SKILL.md skills/context-checkpoint/templates/SESSION.template.md
WORKFLOW_SOURCES := .github/workflows/*.yaml

.DEFAULT_GOAL := help

.PHONY: help
help: ## Show this help message
	@printf "\033[1m%-20s\033[0m %s\n" "Target" "Description"
	@printf "%-20s %s\n" "--------------------" "----------------------------------------"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

.PHONY: lint
lint: lint-yaml lint-json lint-md lint-python lint-workflows lint-hooks ## Run all repository linters

.PHONY: lint-yaml
lint-yaml: ## Check YAML files with yamlfmt and yamllint
	@echo "==> Running yamllint..."
	yamllint -c .yamllint.yaml .
	@echo "==> Running yamlfmt check..."
	yamlfmt -lint .

.PHONY: lint-json
lint-json: ## Validate JSON files
	@echo "==> Validating JSON files..."
	@for f in $(JSON_SOURCES); do \
		python3 -m json.tool "$$f" > /dev/null || exit 1; \
	done

.PHONY: lint-md
lint-md: ## Check Markdown files with pymarkdownlnt
	@echo "==> Running pymarkdownlnt..."
	uv tool run pymarkdownlnt --config .pymarkdown.json scan $(MD_SOURCES)

.PHONY: lint-python
lint-python: ## Check Python files with ruff and ty
	@echo "==> Running ruff check..."
	ruff check $(PYTHON_SOURCES)
	@echo "==> Running ty type check..."
	uv tool run ty check $(PYTHON_SOURCES)

.PHONY: lint-workflows
lint-workflows: ## Check GitHub Actions workflows with actionlint and zizmor
	@echo "==> Running actionlint..."
	actionlint $(WORKFLOW_SOURCES)
	@echo "==> Running zizmor audit..."
	uv tool run zizmor .

.PHONY: lint-hooks
lint-hooks: ## Run prek git hook validation across repository
	@echo "==> Running prek check..."
	uv tool run prek run --all-files

.PHONY: format
format: format-yaml format-json format-md format-python ## Format all files in the repository

.PHONY: format-yaml
format-yaml: ## Format YAML files with yamlfmt
	@echo "==> Formatting YAML with yamlfmt..."
	yamlfmt .

.PHONY: format-json
format-json: ## Format JSON files
	@echo "==> Formatting JSON files..."
	@for f in $(JSON_SOURCES); do \
		python3 -m json.tool "$$f" "$$f.tmp" && mv "$$f.tmp" "$$f"; \
	done

.PHONY: format-md
format-md: ## Format Markdown files with pymarkdownlnt
	@echo "==> Formatting Markdown with pymarkdownlnt..."
	uv tool run pymarkdownlnt --config .pymarkdown.json fix $(MD_SOURCES)

.PHONY: format-python
format-python: ## Format Python files with ruff
	@echo "==> Formatting Python with ruff..."
	ruff format $(PYTHON_SOURCES)
	ruff check --fix $(PYTHON_SOURCES)

.PHONY: setup-hooks
setup-hooks: ## Install git hooks using prek
	@echo "==> Installing git hooks with prek..."
	uv tool run prek install

.PHONY: test-unit
test-unit: ## Run unit tests
	@echo "==> Running unit tests..."
	python3 -m unittest discover tests
	@echo "Unit tests passed."

.PHONY: test-smoke
test-smoke: ## Run smoke tests
	@echo "==> Running smoke tests..."
	python3 installer.py --help > /dev/null
	python3 skills/context-checkpoint/scripts/checkpoint.py --help > /dev/null
	@echo "Smoke tests passed."

.PHONY: test
test: test-unit test-smoke ## Run all tests (unit and smoke)
