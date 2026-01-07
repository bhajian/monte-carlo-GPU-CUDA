# Usage

## Prerequisites

- Docker (or podman) to build images
- kubectl configured for your cluster
- Helm 3 for operator installs

## Build images

From repo root:

```bash
./scripts/build-images.sh
```

Update the image names in `deploy/manifests/service-deployment.yaml`,
`deploy/manifests/callback-deployment.yaml`, and `deploy/templates/*.yaml`.

## Install GPU/NCCL/NFD/MPI/SR-IOV operators

```bash
./operators/install.sh
```

## Deploy service + callback

```bash
./deploy/deploy.sh
```

## Submit a job

```bash
kubectl -n montecarlo port-forward svc/montecarlo-service 8080:8080

curl -X POST http://localhost:8080/jobs \
  -H 'Content-Type: application/json' \
  -d '{
    "simulation": "pi",
    "num_simulations": 2000000,
    "mode": "single-gpu",
    "workers": 1,
    "gpus_per_worker": 1,
    "callback_url": "http://montecarlo-callback.montecarlo.svc.cluster.local:8090/callback"
  }'
```

## Multi-GPU (single node)

```bash
curl -X POST http://localhost:8080/jobs \
  -H 'Content-Type: application/json' \
  -d '{
    "simulation": "option_price",
    "hyperparams": {"spot": 120, "strike": 100, "vol": 0.3, "rate": 0.04},
    "num_simulations": 3000000,
    "mode": "multi-gpu",
    "workers": 1,
    "gpus_per_worker": 4,
    "callback_url": "http://montecarlo-callback.montecarlo.svc.cluster.local:8090/callback"
  }'
```

## Multi-node (MPI/NCCL)

```bash
curl -X POST http://localhost:8080/jobs \
  -H 'Content-Type: application/json' \
  -d '{
    "simulation": "pi",
    "num_simulations": 5000000,
    "mode": "multi-node",
    "nodes": 4,
    "gpus_per_worker": 1,
    "callback_url": "http://montecarlo-callback.montecarlo.svc.cluster.local:8090/callback"
  }'
```

## Callback storage

Set `S3_BUCKET` on the callback deployment to write results to S3.
If unset, results are written to `/data/results` inside the callback container.

## Environment variables

Service container:
- `WORKER_IMAGE` – default worker image
- `DEFAULT_CALLBACK_URL` – fallback callback URL
- `NAMESPACE` – Kubernetes namespace to create jobs
- `MPI_API_VERSION` – MPIJob API version (default `v2beta1`)

Worker container:
- `NUM_SIMULATIONS` – total samples
- `SIMULATION` – `pi` or `option_price`
- `PAYLOAD_JSON` – arbitrary JSON payload
- `HYPERPARAMS_JSON` – hyperparameters JSON
- `CALLBACK_URL` – where to post results
- `RUN_ID` – run identifier
- `FORCE_CPU=1` – force CPU path
