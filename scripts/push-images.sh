#!/usr/bin/env bash
set -euo pipefail

REGISTRY=${REGISTRY:-ghcr.io/example}
TAG=${TAG:-latest}

for image in montecarlo-service montecarlo-worker montecarlo-callback; do
  docker push "${REGISTRY}/${image}:${TAG}"
done

echo "Images pushed to ${REGISTRY}."
