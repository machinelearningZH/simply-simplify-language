#!/usr/bin/env bash

set -euo pipefail

if [[ ! -f Dockerfile ]]; then
    echo "No Dockerfile found; skipping container validation."
    exit 0
fi

if ! command -v docker >/dev/null 2>&1; then
    if [[ "${REQUIRE_CONTAINER_BUILD:-0}" == "1" ]]; then
        echo "Docker is required but is not installed." >&2
        exit 1
    fi
    echo "Docker is not installed; CI will perform the required container validation."
    exit 0
fi

for compose_file in compose.yaml compose.yml docker-compose.yaml docker-compose.yml; do
    if [[ -f "${compose_file}" ]]; then
        docker compose --file "${compose_file}" config --quiet
        break
    fi
done

if ! docker info >/dev/null 2>&1; then
    if [[ "${REQUIRE_CONTAINER_BUILD:-0}" == "1" ]]; then
        echo "Docker is required but its daemon is unavailable." >&2
        exit 1
    fi
    echo "Docker is unavailable; CI will perform the required container build."
    exit 0
fi

docker build --tag local/simply-simplify-language:validation .
