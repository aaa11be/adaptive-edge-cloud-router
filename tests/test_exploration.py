import pytest

from edge_cloud_router.routing.exploration import (
    select_exploration_endpoint,
)
from edge_cloud_router.routing.latency_estimator import (
    LatencyEstimator,
)
from edge_cloud_router.schemas import RoutingContext


def make_context(
    *,
    minimum_quality_score: float = 0.5,
    privacy_required: bool = False,
    cloud_available: bool = True,
) -> RoutingContext:
    return RoutingContext(
        estimated_local_latency_ms=3000.0,
        estimated_cloud_latency_ms=1000.0,
        local_load_ratio=0.2,
        minimum_quality_score=minimum_quality_score,
        privacy_required=privacy_required,
        cloud_available=cloud_available,
        cloud_probe_latency_ms=400.0,
    )


def test_exploration_selects_local_first_on_tie() -> None:
    estimator = LatencyEstimator()

    endpoint = select_exploration_endpoint(
        context=make_context(),
        estimator=estimator,
    )

    assert endpoint == "local"


def test_exploration_selects_cloud_after_local_observation() -> None:
    estimator = LatencyEstimator(
        local_observation_count=1,
        cloud_observation_count=0,
    )

    endpoint = select_exploration_endpoint(
        context=make_context(),
        estimator=estimator,
    )

    assert endpoint == "cloud"


def test_exploration_returns_none_when_counts_are_sufficient() -> None:
    estimator = LatencyEstimator(
        local_observation_count=1,
        cloud_observation_count=1,
    )

    endpoint = select_exploration_endpoint(
        context=make_context(),
        estimator=estimator,
    )

    assert endpoint is None


def test_exploration_does_not_select_cloud_for_private_request() -> None:
    estimator = LatencyEstimator(
        local_observation_count=1,
        cloud_observation_count=0,
    )

    endpoint = select_exploration_endpoint(
        context=make_context(
            privacy_required=True,
        ),
        estimator=estimator,
    )

    assert endpoint is None


def test_exploration_does_not_select_unavailable_cloud() -> None:
    estimator = LatencyEstimator(
        local_observation_count=1,
        cloud_observation_count=0,
    )

    endpoint = select_exploration_endpoint(
        context=make_context(
            cloud_available=False,
        ),
        estimator=estimator,
    )

    assert endpoint is None


def test_exploration_respects_quality_requirement() -> None:
    estimator = LatencyEstimator(
        local_observation_count=0,
        cloud_observation_count=0,
    )

    endpoint = select_exploration_endpoint(
        context=make_context(
            minimum_quality_score=0.8,
        ),
        estimator=estimator,
    )

    assert endpoint == "cloud"


def test_exploration_uses_configured_minimum_count() -> None:
    estimator = LatencyEstimator(
        local_observation_count=2,
        cloud_observation_count=1,
    )

    endpoint = select_exploration_endpoint(
        context=make_context(),
        estimator=estimator,
        minimum_observations=3,
    )

    assert endpoint == "cloud"


@pytest.mark.parametrize(
    "minimum_observations",
    [
        0,
        -1,
    ],
)
def test_exploration_rejects_invalid_minimum(
    minimum_observations: int,
) -> None:
    with pytest.raises(
        ValueError,
        match=(
            "minimum_observations must be greater than 0"
        ),
    ):
        select_exploration_endpoint(
            context=make_context(),
            estimator=LatencyEstimator(),
            minimum_observations=minimum_observations,
        )