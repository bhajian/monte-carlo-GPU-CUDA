# Architecture

1. Client submits a job to the service API with simulation parameters.
2. Service creates a Kubernetes Job (single/multi-GPU) or MPIJob (multi-node).
3. Worker container runs the Monte Carlo simulation on GPU(s).
4. Results are posted to the callback API, which stores them in S3.

The worker is embarrassingly parallel and supports:
- Single GPU (CUDA)
- Multi-GPU on one node (CUDA per device)
- Multi-node MPI (NCCL-ready if provided in the base image)
