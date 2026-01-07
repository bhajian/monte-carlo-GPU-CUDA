from __future__ import annotations

import json
import math
import os
import socket
import time
from typing import Any, Dict, Tuple

import numpy as np
import requests

try:
    import cupy as cp
except Exception:
    cp = None

try:
    from mpi4py import MPI
except Exception:
    MPI = None


def _get_world() -> Tuple[int, int, Any]:
    if MPI is not None:
        comm = MPI.COMM_WORLD
        return comm.Get_rank(), comm.Get_size(), comm
    rank = int(os.getenv("OMPI_COMM_WORLD_RANK", "0"))
    size = int(os.getenv("OMPI_COMM_WORLD_SIZE", "1"))
    return rank, size, None


def _select_backend() -> str:
    if os.getenv("FORCE_CPU") == "1":
        return "cpu"
    if cp is not None:
        return "cuda"
    return "cpu"


def _available_devices() -> int:
    if cp is None:
        return 0
    try:
        return cp.cuda.runtime.getDeviceCount()
    except Exception:
        return 0


def _pi_simulation(samples: int, xp) -> Dict[str, Any]:
    x = xp.random.random(samples)
    y = xp.random.random(samples)
    inside = (x * x + y * y) <= 1.0
    hits = int(inside.sum())
    pi_est = 4.0 * hits / samples
    return {"estimate": float(pi_est), "hits": hits, "samples": samples}


def _option_price(samples: int, xp, hyperparams: Dict[str, Any]) -> Dict[str, Any]:
    spot = float(hyperparams.get("spot", 100.0))
    strike = float(hyperparams.get("strike", 100.0))
    rate = float(hyperparams.get("rate", 0.05))
    vol = float(hyperparams.get("vol", 0.2))
    maturity = float(hyperparams.get("maturity", 1.0))

    z = xp.random.standard_normal(samples)
    st = spot * xp.exp((rate - 0.5 * vol * vol) * maturity + vol * math.sqrt(maturity) * z)
    payoff = xp.maximum(st - strike, 0.0)
    price = float(xp.mean(payoff) * math.exp(-rate * maturity))
    return {
        "estimate": price,
        "samples": samples,
        "spot": spot,
        "strike": strike,
        "rate": rate,
        "vol": vol,
        "maturity": maturity,
    }


def _run_on_devices(simulation: str, samples: int, hyperparams: Dict[str, Any]) -> Dict[str, Any]:
    if cp is None:
        return _run_cpu(simulation, samples, hyperparams)

    device_count = _available_devices()
    if device_count <= 1:
        with cp.cuda.Device(0):
            return _run_cuda(simulation, samples, hyperparams)

    per_device = samples // device_count
    remainder = samples % device_count
    results = []
    for device_id in range(device_count):
        local_samples = per_device + (1 if device_id < remainder else 0)
        if local_samples == 0:
            continue
        with cp.cuda.Device(device_id):
            results.append(_run_cuda(simulation, local_samples, hyperparams))

    if simulation == "pi":
        total_hits = sum(r["hits"] for r in results)
        total_samples = sum(r["samples"] for r in results)
        return {
            "estimate": 4.0 * total_hits / total_samples,
            "hits": total_hits,
            "samples": total_samples,
        }

    estimates = [r["estimate"] for r in results]
    return {
        "estimate": float(np.mean(estimates)),
        "samples": sum(r["samples"] for r in results),
    }


def _run_cuda(simulation: str, samples: int, hyperparams: Dict[str, Any]) -> Dict[str, Any]:
    if simulation == "option_price":
        return _option_price(samples, cp, hyperparams)
    return _pi_simulation(samples, cp)


def _run_cpu(simulation: str, samples: int, hyperparams: Dict[str, Any]) -> Dict[str, Any]:
    if simulation == "option_price":
        return _option_price(samples, np, hyperparams)
    return _pi_simulation(samples, np)


def _send_callback(callback_url: str, payload: Dict[str, Any]) -> None:
    if not callback_url:
        raise RuntimeError("CALLBACK_URL is required")
    response = requests.post(callback_url, json=payload, timeout=60)
    response.raise_for_status()


def main() -> None:
    payload_json = os.getenv("PAYLOAD_JSON", "{}")
    hyperparams_json = os.getenv("HYPERPARAMS_JSON", "{}")
    num_simulations = int(os.getenv("NUM_SIMULATIONS", "1000000"))
    simulation = os.getenv("SIMULATION", "pi")
    callback_url = os.getenv("CALLBACK_URL", "")
    run_id = os.getenv("RUN_ID", "run")

    payload = json.loads(payload_json)
    hyperparams = json.loads(hyperparams_json)

    rank, world_size, comm = _get_world()
    local_samples = num_simulations // world_size
    if rank == 0:
        local_samples += num_simulations % world_size

    backend = _select_backend()
    start = time.time()
    if backend == "cuda":
        local_result = _run_on_devices(simulation, local_samples, hyperparams)
    else:
        local_result = _run_cpu(simulation, local_samples, hyperparams)

    if simulation == "pi" and comm is not None:
        total_hits = comm.allreduce(local_result["hits"], op=MPI.SUM)
        total_samples = comm.allreduce(local_result["samples"], op=MPI.SUM)
        result = {
            "estimate": 4.0 * total_hits / total_samples,
            "hits": total_hits,
            "samples": total_samples,
        }
    elif comm is not None:
        estimates = comm.allgather(local_result["estimate"])
        result = {
            "estimate": float(np.mean(estimates)),
            "samples": num_simulations,
        }
    else:
        result = local_result

    duration = time.time() - start
    response_payload = {
        "run_id": run_id,
        "simulation": simulation,
        "payload": payload,
        "hyperparams": hyperparams,
        "result": result,
        "backend": backend,
        "world_rank": rank,
        "world_size": world_size,
        "host": socket.gethostname(),
        "duration_seconds": duration,
    }

    _send_callback(callback_url, response_payload)


if __name__ == "__main__":
    main()
