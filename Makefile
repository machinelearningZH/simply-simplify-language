.DEFAULT_GOAL := help

UV ?= uv

.PHONY: help sync install run format format-check lint test check pre-commit docker-build docker-run

IMAGE ?= simply-simplify-language
PORT ?= 8080

help: ## Show available commands.
	@awk 'BEGIN {FS = ":.*## "; printf "Usage: make <target>\n\nTargets:\n"} /^[a-zA-Z_-]+:.*## / {printf "  %-14s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

sync: ## Install dependencies exactly as locked.
	$(UV) sync --locked

install: sync ## Install dependencies and repository hooks.
	$(UV) run pre-commit install --hook-type pre-commit --hook-type pre-push

run: ## Run the Streamlit app locally.
	$(UV) run streamlit run _streamlit_app/sprache-vereinfachen.py

format: ## Format Python code.
	$(UV) run ruff format .

format-check: ## Check formatting without modifying files.
	$(UV) run ruff format --check .

lint: ## Run static analysis.
	$(UV) run ruff check .

test: ## Run the test suite.
	$(UV) run pytest

check: format-check lint test ## Run all non-mutating quality checks.

pre-commit: ## Run every configured pre-commit hook.
	$(UV) run pre-commit run --all-files

docker-build: ## Build the Docker image.
	docker build -t $(IMAGE) .

docker-run: ## Run the Docker container.
	docker run --rm -p $(PORT):8501 --env-file _streamlit_app/.env $(IMAGE)
