import httpx
import pytest

from edge_cloud_router.monitoring import state_monitor


def test_measure_local_load_ratio(
    monkeypatch,
) -> None:
    received_intervals: list[float] = []

    def fake_cpu_percent(
        interval: float,
    ) -> float:
        received_intervals.append(interval)
        return 73.5

    monkeypatch.setattr(
        state_monitor.psutil,
        "cpu_percent",
        fake_cpu_percent,
    )

    result = state_monitor.measure_local_load_ratio(
        sample_interval_s=0.2,
    )

    assert received_intervals == [0.2]
    assert result == pytest.approx(0.735)


def test_measure_local_load_ratio_rejects_non_positive_interval(
) -> None:
    with pytest.raises(
        ValueError,
        match="sample_interval_s must be greater than 0",
    ):
        state_monitor.measure_local_load_ratio(
            sample_interval_s=0.0,
        )


def test_measure_endpoint_latency_ms_uses_median(
    monkeypatch,
) -> None:
    requested_urls: list[str] = []

    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

    class FakeClient:
        def get(
            self,
            url: str,
        ) -> FakeResponse:
            requested_urls.append(url)
            return FakeResponse()

    timestamps_ns = iter(
        [
            1_000_000_000,
            1_010_000_000,
            2_000_000_000,
            2_030_000_000,
            3_000_000_000,
            3_020_000_000,
        ]
    )

    monkeypatch.setattr(
        state_monitor,
        "STATE_HTTP_CLIENT",
        FakeClient(),
    )
    monkeypatch.setattr(
        state_monitor.time,
        "perf_counter_ns",
        lambda: next(timestamps_ns),
    )

    result = state_monitor.measure_endpoint_latency_ms(
        url="http://cloud.example/remote-health",
        samples=3,
        warmup_requests=1,
    )

    assert requested_urls == [
        "http://cloud.example/remote-health",
        "http://cloud.example/remote-health",
        "http://cloud.example/remote-health",
        "http://cloud.example/remote-health",
    ]
    assert result == pytest.approx(20.0)


@pytest.mark.parametrize(
    (
        "samples",
        "warmup_requests",
        "expected_message",
    ),
    [
        (
            0,
            1,
            "samples must be greater than 0",
        ),
        (
            3,
            -1,
            "warmup_requests must not be negative",
        ),
    ],
)
def test_measure_endpoint_latency_ms_rejects_invalid_counts(
    samples: int,
    warmup_requests: int,
    expected_message: str,
) -> None:
    with pytest.raises(
        ValueError,
        match=expected_message,
    ):
        state_monitor.measure_endpoint_latency_ms(
            url="http://cloud.example/remote-health",
            samples=samples,
            warmup_requests=warmup_requests,
        )


def test_build_routing_context_uses_estimates_and_probe(
    monkeypatch,
) -> None:
    received_cpu_intervals: list[float] = []
    received_probe_arguments: list[
        tuple[str, int, int]
    ] = []

    def fake_measure_local_load_ratio(
        sample_interval_s: float,
    ) -> float:
        received_cpu_intervals.append(sample_interval_s)
        return 0.73

    def fake_measure_endpoint_latency_ms(
        url: str,
        samples: int,
        warmup_requests: int,
    ) -> float:
        received_probe_arguments.append(
            (
                url,
                samples,
                warmup_requests,
            )
        )
        return 424.5

    monkeypatch.setattr(
        state_monitor,
        "measure_local_load_ratio",
        fake_measure_local_load_ratio,
    )
    monkeypatch.setattr(
        state_monitor,
        "measure_endpoint_latency_ms",
        fake_measure_endpoint_latency_ms,
    )

    context = state_monitor.build_routing_context(
        minimum_quality_score=0.8,
        privacy_required=False,
        estimated_local_latency_ms=2500.0,
        estimated_cloud_latency_ms=1100.0,
        cloud_probe_url=(
            "http://cloud.example/remote-health"
        ),
        cpu_sample_interval_s=0.25,
        probe_samples=5,
        probe_warmup_requests=2,
    )

    assert received_cpu_intervals == [0.25]
    assert received_probe_arguments == [
        (
            "http://cloud.example/remote-health",
            5,
            2,
        )
    ]

    assert context.model_dump() == {
        "estimated_local_latency_ms": 2500.0,
        "estimated_cloud_latency_ms": 1100.0,
        "local_load_ratio": 0.73,
        "minimum_quality_score": 0.8,
        "privacy_required": False,
        "cloud_available": True,
        "cloud_probe_latency_ms": 424.5,
    }


def test_build_routing_context_marks_cloud_unavailable(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        state_monitor,
        "measure_local_load_ratio",
        lambda sample_interval_s: 0.2,
    )

    def fake_failed_probe(
        url: str,
        samples: int,
        warmup_requests: int,
    ) -> float:
        request = httpx.Request(
            "GET",
            url,
        )
        raise httpx.ConnectError(
            "cloud unavailable",
            request=request,
        )

    monkeypatch.setattr(
        state_monitor,
        "measure_endpoint_latency_ms",
        fake_failed_probe,
    )

    context = state_monitor.build_routing_context(
        minimum_quality_score=0.5,
    )

    assert context.cloud_available is False
    assert context.cloud_probe_latency_ms is None
    assert (
        context.estimated_local_latency_ms
        == state_monitor.DEFAULT_LOCAL_LATENCY_ESTIMATE_MS
    )
    assert (
        context.estimated_cloud_latency_ms
        == state_monitor.DEFAULT_CLOUD_LATENCY_ESTIMATE_MS
    )

def test_build_routing_context_skips_probe_for_private_request(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        state_monitor,
        "measure_local_load_ratio",
        lambda sample_interval_s: 0.25,
    )

    def fail_if_probe_runs(
        url: str,
        samples: int,
        warmup_requests: int,
    ) -> float:
        raise AssertionError(
            "cloud probe must not run for a private request"
        )

    monkeypatch.setattr(
        state_monitor,
        "measure_endpoint_latency_ms",
        fail_if_probe_runs,
    )

    context = state_monitor.build_routing_context(
        minimum_quality_score=0.5,
        privacy_required=True,
        estimated_local_latency_ms=2500.0,
        estimated_cloud_latency_ms=1100.0,
        cpu_sample_interval_s=0.1,
        probe_samples=3,
        probe_warmup_requests=1,
    )

    assert context.privacy_required is True
    assert context.cloud_available is True
    assert context.cloud_probe_latency_ms is None
    assert context.local_load_ratio == 0.25
    assert context.estimated_local_latency_ms == 2500.0
    assert context.estimated_cloud_latency_ms == 1100.0