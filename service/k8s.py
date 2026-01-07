from __future__ import annotations

import os
from typing import Dict, Optional

from kubernetes import client, config


def _load_kube_config() -> None:
    if os.getenv("KUBERNETES_SERVICE_HOST"):
        config.load_incluster_config()
    else:
        config.load_kube_config()


class K8sLauncher:
    def __init__(self) -> None:
        _load_kube_config()
        self.namespace = os.getenv("NAMESPACE", "default")
        self.worker_image = os.getenv("WORKER_IMAGE", "ghcr.io/example/montecarlo-worker:latest")
        self.mpi_api_version = os.getenv("MPI_API_VERSION", "v2beta1")

    def launch(
        self,
        job_name: str,
        mode: str,
        workers: int,
        gpus_per_worker: int,
        nodes: int,
        env: Dict[str, str],
        image: Optional[str] = None,
    ) -> None:
        mode = mode.lower()
        image = image or self.worker_image
        if mode == "multi-node":
            self._launch_mpi_job(job_name, nodes, gpus_per_worker, env, image)
        else:
            self._launch_job(job_name, workers, gpus_per_worker, env, image)

    def _launch_job(
        self,
        job_name: str,
        workers: int,
        gpus_per_worker: int,
        env: Dict[str, str],
        image: str,
    ) -> None:
        batch_api = client.BatchV1Api()
        job_manifest = {
            "apiVersion": "batch/v1",
            "kind": "Job",
            "metadata": {"name": job_name, "namespace": self.namespace},
            "spec": {
                "completions": workers,
                "parallelism": workers,
                "backoffLimit": 0,
                "template": {
                    "metadata": {"labels": {"app": job_name}},
                    "spec": {
                        "restartPolicy": "Never",
                        "containers": [
                            {
                                "name": "worker",
                                "image": image,
                                "imagePullPolicy": "IfNotPresent",
                                "env": [
                                    {"name": key, "value": value}
                                    for key, value in env.items()
                                ],
                                "resources": {
                                    "limits": {"nvidia.com/gpu": gpus_per_worker}
                                },
                            }
                        ],
                    },
                },
            },
        }
        batch_api.create_namespaced_job(namespace=self.namespace, body=job_manifest)

    def _launch_mpi_job(
        self,
        job_name: str,
        nodes: int,
        gpus_per_worker: int,
        env: Dict[str, str],
        image: str,
    ) -> None:
        custom_api = client.CustomObjectsApi()
        mpi_job = {
            "apiVersion": f"kubeflow.org/{self.mpi_api_version}",
            "kind": "MPIJob",
            "metadata": {"name": job_name, "namespace": self.namespace},
            "spec": {
                "slotsPerWorker": gpus_per_worker,
                "cleanPodPolicy": "Running",
                "mpiReplicaSpecs": {
                    "Launcher": {
                        "replicas": 1,
                        "template": {
                            "spec": {
                                "containers": [
                                    {
                                        "name": "launcher",
                                        "image": image,
                                        "imagePullPolicy": "IfNotPresent",
                                        "env": [
                                            {"name": key, "value": value}
                                            for key, value in env.items()
                                        ],
                                    }
                                ]
                            }
                        },
                    },
                    "Worker": {
                        "replicas": nodes,
                        "template": {
                            "spec": {
                                "containers": [
                                    {
                                        "name": "worker",
                                        "image": image,
                                        "imagePullPolicy": "IfNotPresent",
                                        "env": [
                                            {"name": key, "value": value}
                                            for key, value in env.items()
                                        ],
                                        "resources": {
                                            "limits": {"nvidia.com/gpu": gpus_per_worker}
                                        },
                                    }
                                ]
                            }
                        },
                    },
                },
            },
        }
        custom_api.create_namespaced_custom_object(
            group="kubeflow.org",
            version=self.mpi_api_version,
            namespace=self.namespace,
            plural="mpijobs",
            body=mpi_job,
        )
