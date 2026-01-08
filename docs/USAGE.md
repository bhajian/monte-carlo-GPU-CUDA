# Usage

## Prerequisites

- Docker (or podman) to build images
- kubectl configured for your cluster
- Helm 3 for operator installs

## Execution flavors

This stack supports two flavors:

1) Single GPU / single node: run one worker container with `--gpus` on a single machine.
2) SOA with leader worker nodes: run the API service to launch worker Jobs, or use MPI for
   multi-node runs where rank 0 acts as the leader and other ranks are worker nodes.

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

## Run a worker directly (single node)

The worker is a one-shot container: it reads env vars, runs, posts results to the callback,
and exits. This is useful for a simple local run without the service API.

```bash
docker build -t montecarlo-worker ./worker
docker build -t montecarlo-callback ./callback

docker network create montecarlo
docker run -d --name mc-callback --network montecarlo -p 8090:8090 montecarlo-callback

docker run --rm --network montecarlo \
  -e SIMULATION=pi \
  -e NUM_SIMULATIONS=1000000 \
  -e RUN_ID=local-1 \
  -e CALLBACK_URL=http://mc-callback:8090/callback \
  -e FORCE_CPU=1 \
  montecarlo-worker
```

Notes:
- For GPU: add `--gpus all` and drop `FORCE_CPU=1`.
- For option pricing: set `SIMULATION=option_price` and `HYPERPARAMS_JSON='{"spot":120,"strike":100,"vol":0.3,"rate":0.04}'`.

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
