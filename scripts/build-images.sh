#!/usr/bin/env bash
set -euo pipefail

REGISTRY=${REGISTRY:-ghcr.io/example}
TAG=${TAG:-latest}

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

docker build -t "${REGISTRY}/montecarlo-service:${TAG}" "${ROOT_DIR}/service"
docker build -t "${REGISTRY}/montecarlo-worker:${TAG}" "${ROOT_DIR}/worker"
docker build -t "${REGISTRY}/montecarlo-callback:${TAG}" "${ROOT_DIR}/callback"

echo "Images built with tag ${TAG} under ${REGISTRY}."
