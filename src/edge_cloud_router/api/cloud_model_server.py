import time

from edge_cloud_router.api.app_factory import create_app
from edge_cloud_router.inference.cloud_model_backend import (
    CloudModelBackend,
)


cloud_model_backend = CloudModelBackend(
    max_tokens=64,
    temperature=0.0,
    quality_score=0.90,
)

app = create_app(
    title="Adaptive Edge-Cloud Router Cloud Model API",
    backend=cloud_model_backend,
)


@app.get("/remote-health")
def remote_health() -> dict[str, str | float]:
    """Check the actual remote inference provider."""

    start_ns = time.perf_counter_ns()

    output_text = cloud_model_backend.probe()

    end_ns = time.perf_counter_ns()

    remote_latency_ms = (
        end_ns - start_ns
    ) / 1_000_000

    return {
        "status": "ok",
        "model": cloud_model_backend.model_name,
        "output": output_text,
        "remote_latency_ms": remote_latency_ms,
    }