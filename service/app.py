from __future__ import annotations

import json
import os
import uuid
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from k8s import K8sLauncher


app = FastAPI(title="MonteCarloCuda Service", version="0.1.0")
launcher = K8sLauncher()


class JobRequest(BaseModel):
    job_name: Optional[str] = None
    payload: Dict[str, Any] = Field(default_factory=dict)
    hyperparams: Dict[str, Any] = Field(default_factory=dict)
    num_simulations: int = Field(default=1_000_000, ge=1)
    simulation: str = Field(default="pi")
    mode: str = Field(default="single-gpu")
    workers: int = Field(default=1, ge=1)
    gpus_per_worker: int = Field(default=1, ge=1)
    nodes: int = Field(default=1, ge=1)
    callback_url: Optional[str] = None
    image: Optional[str] = None


class JobResponse(BaseModel):
    job_name: str
    namespace: str
    mode: str
    workers: int
    gpus_per_worker: int
    nodes: int
    callback_url: str


@app.get("/healthz")
def healthz() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/jobs", response_model=JobResponse)
def submit_job(req: JobRequest) -> JobResponse:
    job_name = req.job_name or f"mc-{uuid.uuid4().hex[:8]}"
    callback_url = req.callback_url or os.getenv("DEFAULT_CALLBACK_URL", "")
    if not callback_url:
        raise HTTPException(status_code=400, detail="callback_url is required")

    env = {
        "PAYLOAD_JSON": json.dumps(req.payload),
        "HYPERPARAMS_JSON": json.dumps(req.hyperparams),
        "NUM_SIMULATIONS": str(req.num_simulations),
        "SIMULATION": req.simulation,
        "CALLBACK_URL": callback_url,
        "RUN_ID": job_name,
    }

    try:
        launcher.launch(
            job_name=job_name,
            mode=req.mode,
            workers=req.workers,
            gpus_per_worker=req.gpus_per_worker,
            nodes=req.nodes,
            env=env,
            image=req.image,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return JobResponse(
        job_name=job_name,
        namespace=launcher.namespace,
        mode=req.mode,
        workers=req.workers,
        gpus_per_worker=req.gpus_per_worker,
        nodes=req.nodes,
        callback_url=callback_url,
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8080")))
