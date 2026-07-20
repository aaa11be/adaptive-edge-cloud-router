from edge_cloud_router.routing.router import (
    select_adaptive_endpoint,
    select_endpoint,
)
from edge_cloud_router.schemas import RoutingContext


def make_context(
    *,
    local_latency_ms: float = 2500.0,
    cloud_latency_ms: float = 1100.0,
    minimum_quality_score: float = 0.5,
    privacy_required: bool = False,
    cloud_available: bool = True,
) -> RoutingContext:
    return RoutingContext(
        estimated_local_latency_ms=local_latency_ms,
        estimated_cloud_latency_ms=cloud_latency_ms,
        local_load_ratio=0.2,
        minimum_quality_score=minimum_quality_score,
        privacy_required=privacy_required,
        cloud_available=cloud_available,
        cloud_probe_latency_ms=400.0,
    )


def test_always_local_strategy() -> None:
    assert select_endpoint("always_local") == "local"


def test_always_cloud_strategy() -> None:
    assert select_endpoint("always_cloud") == "cloud"


def test_adaptive_router_keeps_private_request_local() -> None:
    context = make_context(
        local_latency_ms=3000.0,
        cloud_latency_ms=500.0,
        minimum_quality_score=0.9,
        privacy_required=True,
    )

    assert select_adaptive_endpoint(context) == "local"


def test_adaptive_router_uses_local_when_cloud_unavailable() -> None:
    context = make_context(
        local_latency_ms=3000.0,
        cloud_latency_ms=500.0,
        cloud_available=False,
    )

    assert select_adaptive_endpoint(context) == "local"


def test_adaptive_router_uses_cloud_for_high_quality() -> None:
    context = make_context(
        local_latency_ms=500.0,
        cloud_latency_ms=2000.0,
        minimum_quality_score=0.8,
    )

    assert select_adaptive_endpoint(context) == "cloud"


def test_adaptive_router_uses_faster_cloud() -> None:
    context = make_context(
        local_latency_ms=2500.0,
        cloud_latency_ms=1100.0,
        minimum_quality_score=0.5,
    )

    assert select_adaptive_endpoint(context) == "cloud"


def test_adaptive_router_uses_faster_local() -> None:
    context = make_context(
        local_latency_ms=700.0,
        cloud_latency_ms=1400.0,
        minimum_quality_score=0.5,
    )

    assert select_adaptive_endpoint(context) == "local"


def test_adaptive_router_uses_local_when_latencies_tie() -> None:
    context = make_context(
        local_latency_ms=1000.0,
        cloud_latency_ms=1000.0,
        minimum_quality_score=0.5,
    )

    assert select_adaptive_endpoint(context) == "local"