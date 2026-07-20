import pytest
from pydantic import ValidationError

from edge_cloud_router.schemas import RoutingContext


def test_routing_context_accepts_valid_values() -> None:
    context = RoutingContext(
        estimated_local_latency_ms=2500.0,
        estimated_cloud_latency_ms=1100.0,
        local_load_ratio=0.5,
        minimum_quality_score=0.8,
        privacy_required=False,
        cloud_available=True,
        cloud_probe_latency_ms=400.0,
    )

    assert (
        context.estimated_local_latency_ms
        == 2500.0
    )
    assert (
        context.estimated_cloud_latency_ms
        == 1100.0
    )
    assert context.local_load_ratio == 0.5
    assert context.minimum_quality_score == 0.8
    assert context.privacy_required is False
    assert context.cloud_available is True
    assert context.cloud_probe_latency_ms == 400.0


def test_routing_context_allows_missing_probe() -> None:
    context = RoutingContext(
        estimated_local_latency_ms=2500.0,
        estimated_cloud_latency_ms=1100.0,
        local_load_ratio=0.2,
        minimum_quality_score=0.5,
    )

    assert context.cloud_available is True
    assert context.cloud_probe_latency_ms is None


def test_routing_context_rejects_invalid_ratio() -> None:
    with pytest.raises(ValidationError):
        RoutingContext(
            estimated_local_latency_ms=2500.0,
            estimated_cloud_latency_ms=1100.0,
            local_load_ratio=1.1,
            minimum_quality_score=0.8,
        )


def test_routing_context_rejects_negative_latency() -> None:
    with pytest.raises(ValidationError):
        RoutingContext(
            estimated_local_latency_ms=-1.0,
            estimated_cloud_latency_ms=1100.0,
            local_load_ratio=0.5,
            minimum_quality_score=0.8,
        )