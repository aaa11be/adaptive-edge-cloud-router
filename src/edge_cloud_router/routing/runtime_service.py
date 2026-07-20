from __future__ import annotations

import time

from edge_cloud_router.monitoring.state_monitor import (
    DEFAULT_CLOUD_PROBE_URL,
    DEFAULT_CPU_SAMPLE_INTERVAL_S,
    DEFAULT_PROBE_SAMPLES,
    DEFAULT_PROBE_WARMUP_REQUESTS,
    build_routing_context,
)
from edge_cloud_router.routing.latency_estimator import (
    LatencyEstimator,
)
from edge_cloud_router.routing.service import (
    route_adaptive_inference,
)
from edge_cloud_router.schemas import (
    InferenceRequest,
    InferenceResponse,
    RoutingContext,
)


RUNTIME_LATENCY_ESTIMATOR = LatencyEstimator()


def route_runtime_adaptive_inference(
    *,
    request: InferenceRequest,
    minimum_quality_score: float,
    privacy_required: bool = False,
    cloud_probe_url: str = DEFAULT_CLOUD_PROBE_URL,
    cpu_sample_interval_s: float = (
        DEFAULT_CPU_SAMPLE_INTERVAL_S
    ),
    probe_samples: int = DEFAULT_PROBE_SAMPLES,
    probe_warmup_requests: int = (
        DEFAULT_PROBE_WARMUP_REQUESTS
    ),
    latency_estimator: LatencyEstimator | None = None,
) -> tuple[RoutingContext, InferenceResponse]:
    """Measure state, route inference, and update latency estimates."""

    estimator = (
        latency_estimator
        if latency_estimator is not None
        else RUNTIME_LATENCY_ESTIMATOR
    )

    context = build_routing_context(
        minimum_quality_score=minimum_quality_score,
        privacy_required=privacy_required,
        estimated_local_latency_ms=(
            estimator.get_estimate("local")
        ),
        estimated_cloud_latency_ms=(
            estimator.get_estimate("cloud")
        ),
        cloud_probe_url=cloud_probe_url,
        cpu_sample_interval_s=cpu_sample_interval_s,
        probe_samples=probe_samples,
        probe_warmup_requests=probe_warmup_requests,
    )

    request_start_ns = time.perf_counter_ns()

    response = route_adaptive_inference(
        context,
        request,
    )

    request_end_ns = time.perf_counter_ns()

    observed_latency_ms = (
        request_end_ns - request_start_ns
    ) / 1_000_000

    if response.success:
        estimator.update(
            endpoint=response.endpoint,
            observed_latency_ms=observed_latency_ms,
        )

    return context, response