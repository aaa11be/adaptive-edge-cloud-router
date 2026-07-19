import pytest
from pydantic import ValidationError

from edge_cloud_router.schemas import RoutingContext


def test_routing_context_accepts_valid_values() -> None:
    context = RoutingContext(
        estimated_cloud_rtt_ms=30.0,
        local_load_ratio=0.5,
        minimum_quality_score=0.8,
        privacy_required=False,
    )

    assert context.estimated_cloud_rtt_ms == 30.0
    assert context.local_load_ratio == 0.5
    assert context.minimum_quality_score == 0.8
    assert context.privacy_required is False


def test_routing_context_rejects_invalid_ratio() -> None:
    with pytest.raises(ValidationError):
        RoutingContext(
            estimated_cloud_rtt_ms=30.0,
            local_load_ratio=1.1,
            minimum_quality_score=0.8,
            privacy_required=False,
        )