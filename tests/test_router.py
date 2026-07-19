from edge_cloud_router.routing.router import select_endpoint
from edge_cloud_router.routing.router import (
    select_adaptive_endpoint,
    select_endpoint,
)
from edge_cloud_router.schemas import RoutingContext


def test_always_local_strategy() -> None:
    assert select_endpoint("always_local") == "local"


def test_always_cloud_strategy() -> None:
    assert select_endpoint("always_cloud") == "cloud"

def test_adaptive_router_keeps_private_request_local() -> None:
    context = RoutingContext(
        estimated_cloud_rtt_ms=10.0,
        local_load_ratio=1.0,
        minimum_quality_score=0.9,
        privacy_required=True,
    )

    assert select_adaptive_endpoint(context) == "local"

def test_adaptive_router_uses_cloud_for_high_quality() -> None:
    context = RoutingContext(
        estimated_cloud_rtt_ms=30.0,
        local_load_ratio=0.2,
        minimum_quality_score=0.8,
    )

    assert select_adaptive_endpoint(context) == "cloud"


def test_adaptive_router_uses_cloud_when_local_is_busy() -> None:
    context = RoutingContext(
        estimated_cloud_rtt_ms=30.0,
        local_load_ratio=0.9,
        minimum_quality_score=0.5,
    )

    assert select_adaptive_endpoint(context) == "cloud"


def test_adaptive_router_uses_local_by_default() -> None:
    context = RoutingContext(
        estimated_cloud_rtt_ms=150.0,
        local_load_ratio=0.3,
        minimum_quality_score=0.5,
    )

    assert select_adaptive_endpoint(context) == "local"