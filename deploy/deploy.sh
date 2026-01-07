#!/usr/bin/env bash
set -euo pipefail

kubectl apply -f "$(dirname "$0")/manifests/namespace.yaml"
kubectl apply -f "$(dirname "$0")/manifests/service-rbac.yaml"
kubectl apply -f "$(dirname "$0")/manifests/callback-deployment.yaml"
kubectl apply -f "$(dirname "$0")/manifests/callback-service.yaml"
kubectl apply -f "$(dirname "$0")/manifests/service-deployment.yaml"
kubectl apply -f "$(dirname "$0")/manifests/service-service.yaml"

echo "Service deployed. Use kubectl -n montecarlo get pods to watch startup."
