from edge_cloud_router.monitoring.state_monitor import (
    DEFAULT_CLOUD_HEALTH_URL,
    DEFAULT_CPU_SAMPLE_INTERVAL_S,
    DEFAULT_RTT_SAMPLES,
    DEFAULT_RTT_WARMUP_REQUESTS,
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
    cloud_health_url: str = DEFAULT_CLOUD_HEALTH_URL,
    cpu_sample_interval_s: float = DEFAULT_CPU_SAMPLE_INTERVAL_S,
    rtt_samples: int = DEFAULT_RTT_SAMPLES,
    rtt_warmup_requests: int = DEFAULT_RTT_WARMUP_REQUESTS,
) -> tuple[RoutingContext, InferenceResponse]:
    """Measure runtime state and execute adaptive inference."""

    context = build_routing_context(
        minimum_quality_score=minimum_quality_score,
        privacy_required=privacy_required,
        cloud_health_url=cloud_health_url,
        cpu_sample_interval_s=cpu_sample_interval_s,
        rtt_samples=rtt_samples,
        rtt_warmup_requests=rtt_warmup_requests,
    )

    response = route_adaptive_inference(
        context,
        request,
    )

    return context, response