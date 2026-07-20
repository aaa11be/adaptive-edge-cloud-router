import pytest

from edge_cloud_router.routing.latency_estimator import (
    LatencyEstimator,
)


def test_latency_estimator_returns_initial_values() -> None:
    estimator = LatencyEstimator(
        local_latency_ms=3000.0,
        cloud_latency_ms=1000.0,
        smoothing_factor=0.3,
    )

    assert estimator.get_estimate("local") == 3000.0
    assert estimator.get_estimate("cloud") == 1000.0


def test_latency_estimator_updates_local_with_ewma() -> None:
    estimator = LatencyEstimator(
        local_latency_ms=3000.0,
        cloud_latency_ms=1000.0,
        smoothing_factor=0.3,
    )

    updated = estimator.update(
        endpoint="local",
        observed_latency_ms=2000.0,
    )

    assert updated == pytest.approx(2700.0)
    assert estimator.local_latency_ms == pytest.approx(
        2700.0
    )
    assert estimator.cloud_latency_ms == 1000.0


def test_latency_estimator_updates_cloud_with_ewma() -> None:
    estimator = LatencyEstimator(
        local_latency_ms=3000.0,
        cloud_latency_ms=1000.0,
        smoothing_factor=0.25,
    )

    updated = estimator.update(
        endpoint="cloud",
        observed_latency_ms=1800.0,
    )

    assert updated == pytest.approx(1200.0)
    assert estimator.cloud_latency_ms == pytest.approx(
        1200.0
    )
    assert estimator.local_latency_ms == 3000.0


def test_latency_estimator_applies_repeated_updates() -> None:
    estimator = LatencyEstimator(
        local_latency_ms=3000.0,
        cloud_latency_ms=1000.0,
        smoothing_factor=0.5,
    )

    first = estimator.update(
        endpoint="cloud",
        observed_latency_ms=2000.0,
    )
    second = estimator.update(
        endpoint="cloud",
        observed_latency_ms=3000.0,
    )

    assert first == pytest.approx(1500.0)
    assert second == pytest.approx(2250.0)


@pytest.mark.parametrize(
    (
        "local_latency_ms",
        "cloud_latency_ms",
        "smoothing_factor",
        "expected_message",
    ),
    [
        (
            -1.0,
            1000.0,
            0.3,
            "local_latency_ms must not be negative",
        ),
        (
            3000.0,
            -1.0,
            0.3,
            "cloud_latency_ms must not be negative",
        ),
        (
            3000.0,
            1000.0,
            0.0,
            (
                "smoothing_factor must be greater than 0 "
                "and less than or equal to 1"
            ),
        ),
        (
            3000.0,
            1000.0,
            1.1,
            (
                "smoothing_factor must be greater than 0 "
                "and less than or equal to 1"
            ),
        ),
    ],
)
def test_latency_estimator_rejects_invalid_configuration(
    local_latency_ms: float,
    cloud_latency_ms: float,
    smoothing_factor: float,
    expected_message: str,
) -> None:
    with pytest.raises(
        ValueError,
        match=expected_message,
    ):
        LatencyEstimator(
            local_latency_ms=local_latency_ms,
            cloud_latency_ms=cloud_latency_ms,
            smoothing_factor=smoothing_factor,
        )


def test_latency_estimator_rejects_negative_observation() -> None:
    estimator = LatencyEstimator()

    with pytest.raises(
        ValueError,
        match="observed_latency_ms must not be negative",
    ):
        estimator.update(
            endpoint="local",
            observed_latency_ms=-1.0,
        )

def test_latency_estimator_starts_with_zero_observations() -> None:
    estimator = LatencyEstimator()

    assert estimator.get_observation_count("local") == 0
    assert estimator.get_observation_count("cloud") == 0


def test_latency_estimator_counts_endpoint_observations() -> None:
    estimator = LatencyEstimator(
        local_latency_ms=3000.0,
        cloud_latency_ms=1000.0,
        smoothing_factor=0.3,
    )

    estimator.update(
        endpoint="cloud",
        observed_latency_ms=1200.0,
    )
    estimator.update(
        endpoint="cloud",
        observed_latency_ms=1400.0,
    )
    estimator.update(
        endpoint="local",
        observed_latency_ms=2500.0,
    )

    assert estimator.get_observation_count("local") == 1
    assert estimator.get_observation_count("cloud") == 2


@pytest.mark.parametrize(
    (
        "local_observation_count",
        "cloud_observation_count",
        "expected_message",
    ),
    [
        (
            -1,
            0,
            "local_observation_count must not be negative",
        ),
        (
            0,
            -1,
            "cloud_observation_count must not be negative",
        ),
    ],
)
def test_latency_estimator_rejects_negative_observation_count(
    local_observation_count: int,
    cloud_observation_count: int,
    expected_message: str,
) -> None:
    with pytest.raises(
        ValueError,
        match=expected_message,
    ):
        LatencyEstimator(
            local_observation_count=local_observation_count,
            cloud_observation_count=cloud_observation_count,
        )