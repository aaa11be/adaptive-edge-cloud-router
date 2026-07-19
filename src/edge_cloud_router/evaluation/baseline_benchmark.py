import time
from typing import Any
from statistics import mean, median
from math import ceil

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

def run_benchmark(
    strategy: RoutingStrategy,
    num_requests: int,
) -> list[dict[str, Any]]:
    return [
        run_single_request(strategy, request_index)
        for request_index in range(1, num_requests + 1)
    ]

def summarize_results(
    results: list[dict[str, Any]],
) -> dict[str, float]:
    latencies = sorted(
        result["end_to_end_latency_ms"]
        for result in results
    )

    p95_index = ceil(len(latencies) * 0.95) - 1

    return {
        "mean_latency_ms": mean(latencies),
        "p50_latency_ms": median(latencies),
        "p95_latency_ms": latencies[p95_index],
    }