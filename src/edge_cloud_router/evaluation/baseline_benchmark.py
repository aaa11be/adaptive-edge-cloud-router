import time
import json


from typing import Any
from statistics import mean, median
from math import ceil
from pathlib import Path
from edge_cloud_router.routing.router import RoutingStrategy
from edge_cloud_router.routing.service import (
    route_adaptive_inference,
    route_inference,
)
from edge_cloud_router.schemas import (
    InferenceRequest,
    RoutingContext,
)


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

def run_single_contextual_fixed_request(
    strategy: RoutingStrategy,
    context: RoutingContext,
    request_index: int,
) -> dict[str, Any]:
    request = InferenceRequest(
        request_id=f"{strategy}-{request_index:03d}",
        prompt="What is edge AI?",
        task_type="smoke",
        metadata={"benchmark": "contextual_fixed"},
    )

    start_ns = time.perf_counter_ns()
    response = route_inference(strategy, request)
    end_ns = time.perf_counter_ns()

    end_to_end_latency_ms = (end_ns - start_ns) / 1_000_000

    return {
        "request_id": response.request_id,
        "strategy": strategy,
        "endpoint": response.endpoint,
        "routing_context": context.model_dump(mode="json"),
        "end_to_end_latency_ms": end_to_end_latency_ms,
        "server_processing_ms": response.server_processing_ms,
        "quality_score": response.quality_score,
        "success": response.success,
    }

def run_contextual_fixed_benchmark(
    strategy: RoutingStrategy,
    contexts: list[RoutingContext],
    warmup_requests: int = 0,
) -> list[dict[str, Any]]:
    for request_index in range(1, warmup_requests + 1):
        run_single_request(
            strategy,
            request_index,
        )

    return [
        run_single_contextual_fixed_request(
            strategy,
            context,
            request_index,
        )
        for request_index, context in enumerate(
            contexts,
            start=1,
        )
    ]

def run_single_adaptive_request(
    context: RoutingContext,
    request_index: int,
) -> dict[str, Any]:
    request = InferenceRequest(
        request_id=f"adaptive-{request_index:03d}",
        prompt="What is edge AI?",
        task_type="smoke",
        metadata={"benchmark": "adaptive"},
    )

    start_ns = time.perf_counter_ns()
    response = route_adaptive_inference(context, request)
    end_ns = time.perf_counter_ns()

    end_to_end_latency_ms = (end_ns - start_ns) / 1_000_000

    return {
        "request_id": response.request_id,
        "strategy": "adaptive",
        "endpoint": response.endpoint,
        "routing_context": context.model_dump(mode="json"),
        "end_to_end_latency_ms": end_to_end_latency_ms,
        "server_processing_ms": response.server_processing_ms,
        "quality_score": response.quality_score,
        "success": response.success,
    }

def run_adaptive_benchmark(
    contexts: list[RoutingContext],
    warmup_contexts: list[RoutingContext] | None = None,
) -> list[dict[str, Any]]:
    if warmup_contexts:
        for request_index, context in enumerate(
            warmup_contexts,
            start=1,
        ):
            run_single_adaptive_request(
                context,
                request_index,
            )

    return [
        run_single_adaptive_request(
            context,
            request_index,
        )
        for request_index, context in enumerate(
            contexts,
            start=1,
        )
    ]

def run_benchmark(
    strategy: RoutingStrategy,
    num_requests: int,
    warmup_requests: int = 0,
) -> list[dict[str, Any]]:
    for request_index in range(1, warmup_requests + 1):
        run_single_request(strategy, request_index)

    return [
        run_single_request(strategy, request_index)
        for request_index in range(1, num_requests + 1)
    ]

def summarize_results(
    results: list[dict[str, Any]],
) -> dict[str, float]:
    if not results:
        raise ValueError("results must not be empty")

    latencies = sorted(
        result["end_to_end_latency_ms"]
        for result in results
    )

    server_processing_times = [
        result["server_processing_ms"]
        for result in results
    ]

    quality_scores = [
        result["quality_score"]
        for result in results
    ]

    non_inference_overheads = [
        result["end_to_end_latency_ms"]
        - result["server_processing_ms"]
        for result in results
    ]

    successful_requests = sum(
        1
        for result in results
        if result["success"]
    )

    local_selections = sum(
        1
        for result in results
        if result["endpoint"] == "local"
    )

    cloud_selections = sum(
        1
        for result in results
        if result["endpoint"] == "cloud"
    )

    p95_index = ceil(len(latencies) * 0.95) - 1

    return {
        "mean_latency_ms": mean(latencies),
        "p50_latency_ms": median(latencies),
        "p95_latency_ms": latencies[p95_index],
        "mean_server_processing_ms": mean(
            server_processing_times,
        ),
        "mean_non_inference_overhead_ms": mean(
            non_inference_overheads,
        ),
        "mean_quality_score": mean(quality_scores),
        "success_rate": successful_requests / len(results),
        "local_selection_rate": local_selections / len(results),
        "cloud_selection_rate": cloud_selections / len(results),
    }

def summarize_adaptive_results(
    results: list[dict[str, Any]],
) -> dict[str, float | int]:
    summary: dict[str, float | int] = summarize_results(
        results,
    )

    quality_satisfied_count = sum(
        1
        for result in results
        if result["quality_score"]
        >= result["routing_context"]["minimum_quality_score"]
    )

    privacy_required_count = sum(
        1
        for result in results
        if result["routing_context"]["privacy_required"]
    )

    privacy_violation_count = sum(
        1
        for result in results
        if (
            result["routing_context"]["privacy_required"]
            and result["endpoint"] == "cloud"
        )
    )

    privacy_violation_rate = (
        privacy_violation_count / privacy_required_count
        if privacy_required_count > 0
        else 0.0
    )

    summary.update(
        {
            "quality_satisfied_count": quality_satisfied_count,
            "quality_requirement_satisfaction_rate": (
                quality_satisfied_count / len(results)
            ),
            "privacy_required_count": privacy_required_count,
            "privacy_violation_count": privacy_violation_count,
            "privacy_violation_rate": privacy_violation_rate,
        }
    )

    return summary

def save_results_jsonl(
    results: list[dict[str, Any]],
    output_path: str,
) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as file:
        for result in results:
            file.write(json.dumps(result) + "\n")


def save_summary_json(
    summary: dict[str, float],
    output_path: str,
) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as file:
        json.dump(
            summary,
            file,
            indent=2,
        )