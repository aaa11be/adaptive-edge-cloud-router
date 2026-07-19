import time
from typing import Any

from edge_cloud_router.routing.router import RoutingStrategy
from edge_cloud_router.routing.service import route_inference
from edge_cloud_router.schemas import InferenceRequest


def run_single_request(
    strategy: RoutingStrategy,
    request_index: int,
) -> dict[str, Any]:
    request = InferenceRequest(
        request_id=f"{strategy}-{request_index:03d}",
        prompt="What is edge AI?",
        task_type="smoke",
        metadata={"benchmark": "baseline"},
    )

    start_ns = time.perf_counter_ns()

    response = route_inference(strategy, request)

    end_ns = time.perf_counter_ns()

    end_to_end_latency_ms = (end_ns - start_ns) / 1_000_000

    return {
        "request_id": response.request_id,
        "strategy": strategy,
        "endpoint": response.endpoint,
        "end_to_end_latency_ms": end_to_end_latency_ms,
        "server_processing_ms": response.server_processing_ms,
        "quality_score": response.quality_score,
        "success": response.success,
    }