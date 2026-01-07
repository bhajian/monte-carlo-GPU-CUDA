from __future__ import annotations

import json
import os
import time
from typing import Any, Dict

import boto3
from fastapi import FastAPI


app = FastAPI(title="MonteCarloCuda Callback", version="0.1.0")


@app.get("/healthz")
def healthz() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/callback")
def receive_callback(payload: Dict[str, Any]) -> Dict[str, Any]:
    bucket = os.getenv("S3_BUCKET")
    prefix = os.getenv("S3_PREFIX", "montecarlo/results")
    run_id = payload.get("run_id", "run")
    key = f"{prefix}/{run_id}-{int(time.time())}.json"

    if bucket:
        s3 = boto3.client("s3")
        s3.put_object(Bucket=bucket, Key=key, Body=json.dumps(payload).encode("utf-8"))
        return {"status": "stored", "bucket": bucket, "key": key}

    local_dir = os.getenv("LOCAL_RESULTS_DIR", "/data/results")
    os.makedirs(local_dir, exist_ok=True)
    path = os.path.join(local_dir, f"{run_id}-{int(time.time())}.json")
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle)
    return {"status": "stored", "path": path}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8090")))
