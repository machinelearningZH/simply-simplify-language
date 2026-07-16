FROM ghcr.io/astral-sh/uv:0.11.23 AS uv

FROM python:3.12-slim AS builder
WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*
COPY --from=uv /uv /usr/local/bin/uv

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

FROM python:3.12-slim
WORKDIR /app
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

RUN useradd --create-home --uid 10001 app

COPY --from=builder --chown=app:app /app/.venv ./.venv
COPY --chown=app:app config.yaml ./
COPY --chown=app:app _streamlit_app ./_streamlit_app
RUN test ! -e _streamlit_app/.env

EXPOSE 8501

USER app

HEALTHCHECK --interval=30s --timeout=3s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8501/_stcore/health', timeout=2)"

CMD ["streamlit", "run", "_streamlit_app/sprache-vereinfachen.py", "--server.address=0.0.0.0", "--browser.gatherUsageStats=false"]
