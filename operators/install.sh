#!/usr/bin/env bash
set -euo pipefail

GPU_OPERATOR_NS=${GPU_OPERATOR_NS:-nvidia-gpu-operator}
NFD_NS=${NFD_NS:-node-feature-discovery}
MPI_NS=${MPI_NS:-mpi-operator}
SRIOV_NS=${SRIOV_NS:-sriov-network-operator}

helm repo add nvidia https://nvidia.github.io/gpu-operator
helm repo add nfd https://kubernetes-sigs.github.io/node-feature-discovery/charts
helm repo add kubeflow https://kubeflow.github.io/mpi-operator
helm repo add sriov https://openshift.github.io/sriov-network-operator
helm repo update

kubectl create namespace "${GPU_OPERATOR_NS}" --dry-run=client -o yaml | kubectl apply -f -
helm upgrade --install gpu-operator nvidia/gpu-operator \
  --namespace "${GPU_OPERATOR_NS}" \
  --values "$(dirname "$0")/values-gpu-operator.yaml"

kubectl create namespace "${NFD_NS}" --dry-run=client -o yaml | kubectl apply -f -
helm upgrade --install nfd nfd/node-feature-discovery --namespace "${NFD_NS}"

kubectl create namespace "${MPI_NS}" --dry-run=client -o yaml | kubectl apply -f -
helm upgrade --install mpi-operator kubeflow/mpi-operator --namespace "${MPI_NS}"

kubectl create namespace "${SRIOV_NS}" --dry-run=client -o yaml | kubectl apply -f -
helm upgrade --install sriov-network-operator sriov/sriov-network-operator \
  --namespace "${SRIOV_NS}"

echo "Operators installed. Verify with kubectl get pods -A."
