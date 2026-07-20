from typing import Literal

from edge_cloud_router.schemas import RoutingContext


RouteTarget = Literal["local", "cloud"]
RoutingStrategy = Literal[
    "always_local",
    "always_cloud",
]

LOCAL_QUALITY_SCORE = 0.70
CLOUD_QUALITY_SCORE = 0.90


def select_endpoint(
    strategy: RoutingStrategy,
) -> RouteTarget:
    if strategy == "always_local":
        return "local"

    return "cloud"


def select_adaptive_endpoint(
    context: RoutingContext,
) -> RouteTarget:
    """Select an endpoint using constraints and expected latency."""

    if context.privacy_required:
        return "local"

    if not context.cloud_available:
        return "local"

    local_meets_quality = (
        LOCAL_QUALITY_SCORE
        >= context.minimum_quality_score
    )
    cloud_meets_quality = (
        CLOUD_QUALITY_SCORE
        >= context.minimum_quality_score
    )

    if not local_meets_quality and cloud_meets_quality:
        return "cloud"

    if local_meets_quality and not cloud_meets_quality:
        return "local"

    if not local_meets_quality and not cloud_meets_quality:
        # Neither endpoint satisfies the requested quality.
        # Prefer the endpoint with the higher configured quality.
        return "cloud"

    if (
        context.estimated_cloud_latency_ms
        < context.estimated_local_latency_ms
    ):
        return "cloud"

    return "local"