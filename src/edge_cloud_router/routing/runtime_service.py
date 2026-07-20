from edge_cloud_router.monitoring.state_monitor import (
    DEFAULT_CLOUD_LATENCY_ESTIMATE_MS,
    DEFAULT_CLOUD_PROBE_URL,
    DEFAULT_CPU_SAMPLE_INTERVAL_S,
    DEFAULT_LOCAL_LATENCY_ESTIMATE_MS,
    DEFAULT_PROBE_SAMPLES,
    DEFAULT_PROBE_WARMUP_REQUESTS,
    build_routing_context,
)
from edge_cloud_router.routing.service import (
    route_adaptive_inference,
)
from edge_cloud_router.schemas import (
    InferenceRequest,
    InferenceResponse,
    RoutingContext,
)


def route_runtime_adaptive_inference(
    *,
    request: InferenceRequest,
    minimum_quality_score: float,
    privacy_required: bool = False,
    estimated_local_latency_ms: float = (
        DEFAULT_LOCAL_LATENCY_ESTIMATE_MS
    ),
    estimated_cloud_latency_ms: float = (
        DEFAULT_CLOUD_LATENCY_ESTIMATE_MS
    ),
    cloud_probe_url: str = DEFAULT_CLOUD_PROBE_URL,
    cpu_sample_interval_s: float = (
        DEFAULT_CPU_SAMPLE_INTERVAL_S
    ),
    probe_samples: int = DEFAULT_PROBE_SAMPLES,
    probe_warmup_requests: int = (
        DEFAULT_PROBE_WARMUP_REQUESTS
    ),
) -> tuple[RoutingContext, InferenceResponse]:
    """Measure runtime state and execute adaptive inference."""

    context = build_routing_context(
        minimum_quality_score=minimum_quality_score,
        privacy_required=privacy_required,
        estimated_local_latency_ms=(
            estimated_local_latency_ms
        ),
        estimated_cloud_latency_ms=(
            estimated_cloud_latency_ms
        ),
        cloud_probe_url=cloud_probe_url,
        cpu_sample_interval_s=cpu_sample_interval_s,
        probe_samples=probe_samples,
        probe_warmup_requests=probe_warmup_requests,
    )

    response = route_adaptive_inference(
        context,
        request,
    )

    return context, response