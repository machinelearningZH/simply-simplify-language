.PHONY: help sync run format lint test check docker-build docker-run

IMAGE ?= simply-simplify-language
PORT ?= 8080

help:
	@echo "sync          Install dependencies"
	@echo "run           Run the Streamlit app"
	@echo "format        Format Python code"
	@echo "lint          Check Python code"
	@echo "test          Run tests"
	@echo "check         Check formatting, lint, and tests"
	@echo "docker-build  Build the Docker image"
	@echo "docker-run    Run the Docker container"

sync:
	uv sync

run:
	uv run streamlit run _streamlit_app/sprache-vereinfachen.py

format:
	uv run ruff format .

lint:
	uv run ruff check .

test:
	uv run pytest

check:
	uv run ruff format --check .
	uv run ruff check .
	uv run pytest

docker-build:
	docker build -t $(IMAGE) .

docker-run:
	docker run --rm -p $(PORT):8501 --env-file _streamlit_app/.env $(IMAGE)
