from typing import Literal
from edge_cloud_router.schemas import RoutingContext

RouteTarget = Literal["local", "cloud"]
RoutingStrategy = Literal["always_local", "always_cloud"]

LOCAL_QUALITY_SCORE = 0.60
HIGH_LOCAL_LOAD_RATIO = 0.80
MAX_ACCEPTABLE_CLOUD_RTT_MS = 100.0


def select_endpoint(strategy: RoutingStrategy) -> RouteTarget:
    if strategy == "always_local":
        return "local"

    return "cloud"

def select_adaptive_endpoint(
    context: RoutingContext,
) -> RouteTarget:
    if context.privacy_required:
        return "local"

    if context.minimum_quality_score > LOCAL_QUALITY_SCORE:
        return "cloud"

    if (
        context.local_load_ratio >= HIGH_LOCAL_LOAD_RATIO
        and context.estimated_cloud_rtt_ms
        <= MAX_ACCEPTABLE_CLOUD_RTT_MS
    ):
        return "cloud"

    return "local"