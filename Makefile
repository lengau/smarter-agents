# Makefile for smarter-agents

PROJECT := smarter-agents

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
lint-json: lint-json-syntax lint-json-schema ## Validate JSON syntax and JSON schemas

.PHONY: lint-json-syntax
lint-json-syntax: ## Validate JSON syntax across repository
	@echo "==> Validating JSON syntax..."
	@for f in $$(git ls-files "*.json" ".*.json"); do \
		python3 -m json.tool "$$f" > /dev/null || exit 1; \
	done

.PHONY: lint-json-schema
lint-json-schema: ## Validate JSON schemas against Draft 7 metaschema and validate templates
	@echo "==> Validating JSON metaschemas with check-jsonschema..."
	@schemas=$$(git ls-files "*schema.json" "**/schemas/*.json" | sort -u); \
	if [ -n "$$schemas" ]; then \
		uv tool run check-jsonschema --check-metaschema $$schemas; \
	fi
	@echo "==> Validating JSON templates against schemas..."
	@if [ -f skills/context-checkpoint/schemas/checkpoint.schema.json ] && [ -f skills/context-checkpoint/templates/checkpoint.template.json ]; then \
		uv tool run check-jsonschema --schemafile skills/context-checkpoint/schemas/checkpoint.schema.json skills/context-checkpoint/templates/checkpoint.template.json; \
	fi

.PHONY: lint-md
lint-md: ## Check Markdown files with pymarkdownlnt
	@echo "==> Running pymarkdownlnt..."
	uv tool run pymarkdownlnt --config .pymarkdown.json scan .

.PHONY: lint-python
lint-python: ## Check Python files with ruff and ty
	@echo "==> Running ruff check..."
	ruff check .
	@echo "==> Running ty type check..."
	uv tool run ty check .

.PHONY: lint-workflows
lint-workflows: ## Check GitHub Actions workflows with actionlint and zizmor
	@echo "==> Running actionlint..."
	actionlint
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
	@for f in $$(git ls-files "*.json" ".*.json"); do \
		python3 -m json.tool "$$f" "$$f.tmp" && mv "$$f.tmp" "$$f" || exit 1; \
	done

.PHONY: format-md
format-md: ## Format Markdown files with pymarkdownlnt
	@echo "==> Formatting Markdown with pymarkdownlnt..."
	uv tool run pymarkdownlnt --config .pymarkdown.json fix .

.PHONY: format-python
format-python: ## Format Python files with ruff
	@echo "==> Formatting Python with ruff..."
	ruff format .
	ruff check --fix .

.PHONY: setup-hooks
setup-hooks: ## Install git hooks using prek
	@echo "==> Installing git hooks with prek..."
	uv tool run prek install

.PHONY: test-smoke
test-smoke: ## Run smoke tests
	@echo "==> Running smoke tests..."
	python3 installer.py --help > /dev/null
	@echo "Smoke tests passed."

.PHONY: test
test: test-smoke ## Run tests (alias for test-smoke)
