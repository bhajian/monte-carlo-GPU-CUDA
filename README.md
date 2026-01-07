# MonteCarloCuda

Open-source reference stack for running Monte Carlo simulations on GPUs in Kubernetes.
It includes:

- A Python service API that accepts generic payloads + hyperparameters and launches worker jobs
- A CUDA-enabled worker container for embarrassingly parallel Monte Carlo runs (single GPU, multi-GPU, or multi-node)
- A callback test app that receives results and persists them to S3
- Kubernetes manifests and install scripts
- Operator install materials (GPU Operator, NCCL, NFD, MPI, SR-IOV)
- Terraform scaffolding for AWS EKS, S3, and GPU nodes

## Why CUDA for Monte Carlo

CPU-based Monte Carlo often fans out thousands of tiny tasks that need heavy scheduling.
CUDA batches those paths into a single GPU job, reducing per-task scheduling overhead for small tasks.

![CUDA batching reduces per-task scheduling overhead](docs/images/cuda-batched-montecarlo.svg)

## Repo layout

- `service/` – API service container to accept jobs and launch workers
- `worker/` – CUDA Monte Carlo worker container
- `callback/` – test callback API + S3 sink
- `deploy/` – k8s manifests + deployment scripts
- `operators/` – operator install materials
- `docs/` – usage documentation
- `terraform/` – AWS EKS/S3/GPU node scaffolding
- `scripts/` – helper scripts (build/push)

## Notebooks

- `notebooks/api_evaluation.ipynb` – Calls the service and callback APIs and performs basic checks.

## Quick start

See `docs/USAGE.md` for full instructions.
