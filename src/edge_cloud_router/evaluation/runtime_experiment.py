from __future__ import annotations

import argparse
import json
import time
from datetime import UTC, datetime
from pathlib import Path
from statistics import mean
from typing import Any

import httpx

from edge_cloud_router.monitoring.probe_cache import (
    CloudProbeCache,
)
from edge_cloud_router.routing.latency_estimator import (
    LatencyEstimator,
)
from edge_cloud_router.routing.runtime_service import (
    route_runtime_adaptive_inference,
)
from edge_cloud_router.schemas import InferenceRequest


DEFAULT_PROMPT = (
    "Explain edge AI in one short sentence."
)

LOCAL_INFER_URL = "http://127.0.0.1:8000/infer"
CLOUD_INFER_URL = "http://127.0.0.1:8001/infer"


def run_warmup(
    *,
    client: httpx.Client,
    prompt: str,
) -> list[dict[str, Any]]:
    """Warm up local and cloud endpoints without updating EWMA."""

    results: list[dict[str, Any]] = []

    for endpoint, url in (
        ("local", LOCAL_INFER_URL),
        ("cloud", CLOUD_INFER_URL),
    ):
        request_body = {
            "request_id": f"warmup-{endpoint}-001",
            "prompt": prompt,
            "task_type": "smoke",
        }

        start_ns = time.perf_counter_ns()

        response = client.post(
            url,
            json=request_body,
        )
        response.raise_for_status()

        end_ns = time.perf_counter_ns()

        response_body = response.json()

        results.append(
            {
                "endpoint": endpoint,
                "server_processing_ms": response_body[
                    "server_processing_ms"
                ],
                "client_end_to_end_ms": (
                    end_ns - start_ns
                )
                / 1_000_000,
                "success": response_body["success"],
            }
        )

    return results


def run_measured_requests(
    *,
    prompt: str,
    request_count: int,
) -> tuple[
    list[dict[str, Any]],
    LatencyEstimator,
    CloudProbeCache,
]:
    """Run measured adaptive requests in one process."""

    estimator = LatencyEstimator(
        local_latency_ms=3870.0,
        cloud_latency_ms=1144.0,
        smoothing_factor=0.3,
    )

    probe_cache = CloudProbeCache(
        ttl_s=60.0,
    )

    results: list[dict[str, Any]] = []

    for index in range(1, request_count + 1):
        request = InferenceRequest(
            request_id=f"runtime-{index:03d}",
            prompt=prompt,
            task_type="smoke",
        )

        local_before_ms = estimator.local_latency_ms
        cloud_before_ms = estimator.cloud_latency_ms

        runtime_start_ns = time.perf_counter_ns()

        context, response = (
            route_runtime_adaptive_inference(
                request=request,
                minimum_quality_score=0.5,
                privacy_required=False,
                latency_estimator=estimator,
                probe_cache=probe_cache,
            )
        )

        runtime_end_ns = time.perf_counter_ns()

        results.append(
            {
                "request_id": request.request_id,
                "endpoint": response.endpoint,
                "success": response.success,
                "server_processing_ms": (
                    response.server_processing_ms
                ),
                "runtime_total_ms": (
                    runtime_end_ns - runtime_start_ns
                )
                / 1_000_000,
                "local_estimate_before_ms": (
                    local_before_ms
                ),
                "cloud_estimate_before_ms": (
                    cloud_before_ms
                ),
                "local_estimate_after_ms": (
                    estimator.local_latency_ms
                ),
                "cloud_estimate_after_ms": (
                    estimator.cloud_latency_ms
                ),
                "local_observation_count": (
                    estimator.local_observation_count
                ),
                "cloud_observation_count": (
                    estimator.cloud_observation_count
                ),
                "cloud_available": (
                    context.cloud_available
                ),
                "cloud_probe_latency_ms": (
                    context.cloud_probe_latency_ms
                ),
                "routing_context": context.model_dump(),
            }
        )

    return (
        results,
        estimator,
        probe_cache,
    )


def build_summary(
    *,
    warmup_results: list[dict[str, Any]],
    measured_results: list[dict[str, Any]],
    estimator: LatencyEstimator,
    probe_cache: CloudProbeCache,
) -> dict[str, Any]:
    """Build a compact experiment summary."""

    successful_results = [
        result
        for result in measured_results
        if result["success"]
    ]

    endpoint_counts = {
        "local": sum(
            result["endpoint"] == "local"
            for result in measured_results
        ),
        "cloud": sum(
            result["endpoint"] == "cloud"
            for result in measured_results
        ),
    }

    return {
        "created_at": datetime.now(UTC).isoformat(),
        "warmup_results": warmup_results,
        "request_count": len(measured_results),
        "successful_request_count": len(
            successful_results
        ),
        "endpoint_counts": endpoint_counts,
        "mean_runtime_total_ms": mean(
            result["runtime_total_ms"]
            for result in successful_results
        ),
        "mean_server_processing_ms": mean(
            result["server_processing_ms"]
            for result in successful_results
        ),
        "final_local_estimate_ms": (
            estimator.local_latency_ms
        ),
        "final_cloud_estimate_ms": (
            estimator.cloud_latency_ms
        ),
        "local_observation_count": (
            estimator.local_observation_count
        ),
        "cloud_observation_count": (
            estimator.cloud_observation_count
        ),
        "probe_cache_available": (
            probe_cache.available
        ),
        "probe_cache_latency_ms": (
            probe_cache.latency_ms
        ),
    }


def save_jsonl(
    path: Path,
    records: list[dict[str, Any]],
) -> None:
    """Save one JSON object per line."""

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with path.open(
        "w",
        encoding="utf-8",
    ) as file:
        for record in records:
            file.write(
                json.dumps(
                    record,
                    ensure_ascii=False,
                )
            )
            file.write("\n")


def save_json(
    path: Path,
    data: dict[str, Any],
) -> None:
    """Save formatted JSON."""

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--requests",
        type=int,
        default=5,
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("results/runtime"),
    )
    parser.add_argument(
        "--prompt",
        default=DEFAULT_PROMPT,
    )

    args = parser.parse_args()

    if args.requests <= 0:
        raise ValueError(
            "requests must be greater than 0"
        )

    client = httpx.Client(
        timeout=30.0,
    )

    try:
        warmup_results = run_warmup(
            client=client,
            prompt=args.prompt,
        )
    finally:
        client.close()

    (
        measured_results,
        estimator,
        probe_cache,
    ) = run_measured_requests(
        prompt=args.prompt,
        request_count=args.requests,
    )

    summary = build_summary(
        warmup_results=warmup_results,
        measured_results=measured_results,
        estimator=estimator,
        probe_cache=probe_cache,
    )

    result_path = (
        args.output_dir
        / "adaptive_runtime_results.jsonl"
    )
    summary_path = (
        args.output_dir
        / "adaptive_runtime_summary.json"
    )

    save_jsonl(
        result_path,
        measured_results,
    )
    save_json(
        summary_path,
        summary,
    )

    print(
        f"Saved results: {result_path}"
    )
    print(
        f"Saved summary: {summary_path}"
    )
    print(
        json.dumps(
            summary,
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()