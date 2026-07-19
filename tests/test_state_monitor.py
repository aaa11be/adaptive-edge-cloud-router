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

def test_measure_endpoint_rtt_ms_uses_median(
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

    result = state_monitor.measure_endpoint_rtt_ms(
        url="http://cloud.example/health",
        samples=3,
        warmup_requests=1,
    )

    assert requested_urls == [
        "http://cloud.example/health",
        "http://cloud.example/health",
        "http://cloud.example/health",
        "http://cloud.example/health",
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
def test_measure_endpoint_rtt_ms_rejects_invalid_counts(
    samples: int,
    warmup_requests: int,
    expected_message: str,
) -> None:
    with pytest.raises(
        ValueError,
        match=expected_message,
    ):
        state_monitor.measure_endpoint_rtt_ms(
            url="http://cloud.example/health",
            samples=samples,
            warmup_requests=warmup_requests,
        )

def test_build_routing_context_uses_runtime_measurements(
    monkeypatch,
) -> None:
    received_cpu_intervals: list[float] = []
    received_rtt_arguments: list[tuple[str, int, int]] = []

    def fake_measure_local_load_ratio(
        sample_interval_s: float,
    ) -> float:
        received_cpu_intervals.append(sample_interval_s)
        return 0.73

    def fake_measure_endpoint_rtt_ms(
        url: str,
        samples: int,
        warmup_requests: int,
    ) -> float:
        received_rtt_arguments.append(
            (
                url,
                samples,
                warmup_requests,
            )
        )
        return 24.5

    monkeypatch.setattr(
        state_monitor,
        "measure_local_load_ratio",
        fake_measure_local_load_ratio,
    )
    monkeypatch.setattr(
        state_monitor,
        "measure_endpoint_rtt_ms",
        fake_measure_endpoint_rtt_ms,
    )

    context = state_monitor.build_routing_context(
        minimum_quality_score=0.8,
        privacy_required=True,
        cloud_health_url="http://cloud.example/health",
        cpu_sample_interval_s=0.25,
        rtt_samples=5,
        rtt_warmup_requests=2,
    )

    assert received_cpu_intervals == [0.25]
    assert received_rtt_arguments == [
        (
            "http://cloud.example/health",
            5,
            2,
        )
    ]

    assert context.model_dump() == {
        "estimated_cloud_rtt_ms": 24.5,
        "local_load_ratio": 0.73,
        "minimum_quality_score": 0.8,
        "privacy_required": True,
    }