"""FastAPI layer for HTTP-based cloud mock inference."""

import time

from fastapi import FastAPI

from edge_cloud_router.inference.mock_backend import DeterministicMockBackend
from edge_cloud_router.schemas import InferenceRequest, InferenceResponse

app = FastAPI(title="Adaptive Edge-Cloud Router Cloud API")

cloud_backend = DeterministicMockBackend(
    endpoint="cloud",
    processing_delay_ms=80.0,
    quality_score=0.90,
    configured_rtt_ms=0.0,
    model_name="deterministic-cloud-http-mock-v1",
)

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}

@app.post("/infer", response_model=InferenceResponse)
def infer_endpoint(request: InferenceRequest) -> InferenceResponse:
    start_ns = time.perf_counter_ns()

    response = cloud_backend.infer(request)

    end_ns = time.perf_counter_ns()
    response.server_processing_ms = (end_ns - start_ns) / 1_000_000

    return response