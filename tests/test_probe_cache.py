import pytest

from edge_cloud_router.monitoring.probe_cache import (
    CloudProbeCache,
)


def test_probe_cache_starts_empty() -> None:
    cache = CloudProbeCache(
        ttl_s=10.0,
    )

    assert cache.available is None
    assert cache.latency_ms is None
    assert cache.measured_at_s is None
    assert cache.has_fresh_result(0.0) is False


def test_probe_cache_stores_success() -> None:
    cache = CloudProbeCache(
        ttl_s=10.0,
    )

    cache.store_success(
        latency_ms=424.5,
        measured_at_s=100.0,
    )

    assert cache.available is True
    assert cache.latency_ms == 424.5
    assert cache.measured_at_s == 100.0
    assert cache.has_fresh_result(105.0) is True


def test_probe_cache_stores_failure() -> None:
    cache = CloudProbeCache(
        ttl_s=10.0,
    )

    cache.store_failure(
        measured_at_s=100.0,
    )

    assert cache.available is False
    assert cache.latency_ms is None
    assert cache.measured_at_s == 100.0
    assert cache.has_fresh_result(105.0) is True


def test_probe_cache_expires_at_ttl_boundary() -> None:
    cache = CloudProbeCache(
        ttl_s=10.0,
    )

    cache.store_success(
        latency_ms=400.0,
        measured_at_s=100.0,
    )

    assert cache.has_fresh_result(109.999) is True
    assert cache.has_fresh_result(110.0) is False


def test_probe_cache_rejects_clock_before_measurement() -> None:
    cache = CloudProbeCache(
        ttl_s=10.0,
    )

    cache.store_success(
        latency_ms=400.0,
        measured_at_s=100.0,
    )

    assert cache.has_fresh_result(99.0) is False


@pytest.mark.parametrize(
    "ttl_s",
    [
        0.0,
        -1.0,
    ],
)
def test_probe_cache_rejects_invalid_ttl(
    ttl_s: float,
) -> None:
    with pytest.raises(
        ValueError,
        match="ttl_s must be greater than 0",
    ):
        CloudProbeCache(
            ttl_s=ttl_s,
        )


def test_probe_cache_rejects_negative_success_values() -> None:
    cache = CloudProbeCache()

    with pytest.raises(
        ValueError,
        match="latency_ms must not be negative",
    ):
        cache.store_success(
            latency_ms=-1.0,
            measured_at_s=100.0,
        )

    with pytest.raises(
        ValueError,
        match="measured_at_s must not be negative",
    ):
        cache.store_success(
            latency_ms=400.0,
            measured_at_s=-1.0,
        )


def test_probe_cache_rejects_negative_failure_time() -> None:
    cache = CloudProbeCache()

    with pytest.raises(
        ValueError,
        match="measured_at_s must not be negative",
    ):
        cache.store_failure(
            measured_at_s=-1.0,
        )


def test_probe_cache_rejects_negative_current_time() -> None:
    cache = CloudProbeCache()

    with pytest.raises(
        ValueError,
        match="current_time_s must not be negative",
    ):
        cache.has_fresh_result(-1.0)