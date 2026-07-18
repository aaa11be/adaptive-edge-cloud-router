"""FastAPI layer for HTTP-based mock inference."""

import time

from fastapi import FastAPI

from edge_cloud_router.inference.mock_backend import DeterministicMockBackend
from edge_cloud_router.schemas import InferenceRequest, InferenceResponse

app = FastAPI(title="Adaptive Edge-Cloud Router API")

local_backend = DeterministicMockBackend(
    endpoint="local",
    processing_delay_ms=20.0,
    quality_score=0.60,
    configured_rtt_ms=0.0,
    model_name="deterministic-local-http-mock-v1",
)

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}

@app.post("/infer", response_model=InferenceResponse)
def infer_endpoint(request: InferenceRequest) -> InferenceResponse:
    start_ns = time.perf_counter_ns()

    response = local_backend.infer(request)

    end_ns = time.perf_counter_ns()
    response.server_processing_ms = (end_ns - start_ns) / 1_000_000

    return response


