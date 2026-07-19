import time
from statistics import median

import httpx
import psutil

from edge_cloud_router.schemas import RoutingContext

DEFAULT_CPU_SAMPLE_INTERVAL_S = 0.1

DEFAULT_RTT_SAMPLES = 3
DEFAULT_RTT_WARMUP_REQUESTS = 1
DEFAULT_HTTP_TIMEOUT_S = 2.0

DEFAULT_CLOUD_HEALTH_URL = "http://127.0.0.1:8001/health"

STATE_HTTP_CLIENT = httpx.Client(
    timeout=DEFAULT_HTTP_TIMEOUT_S,
)


def measure_local_load_ratio(
    sample_interval_s: float = DEFAULT_CPU_SAMPLE_INTERVAL_S,
) -> float:
    """Measure system-wide CPU utilization as a 0.0-1.0 ratio."""

    if sample_interval_s <= 0.0:
        raise ValueError(
            "sample_interval_s must be greater than 0"
        )

    cpu_percent = psutil.cpu_percent(
        interval=sample_interval_s,
    )

    load_ratio = cpu_percent / 100.0

    return max(
        0.0,
        min(load_ratio, 1.0),
    )


def measure_endpoint_rtt_ms(
    url: str,
    samples: int = DEFAULT_RTT_SAMPLES,
    warmup_requests: int = DEFAULT_RTT_WARMUP_REQUESTS,
) -> float:
    """Measure median HTTP round-trip latency to an endpoint."""

    if samples <= 0:
        raise ValueError(
            "samples must be greater than 0"
        )

    if warmup_requests < 0:
        raise ValueError(
            "warmup_requests must not be negative"
        )

    for _ in range(warmup_requests):
        response = STATE_HTTP_CLIENT.get(url)
        response.raise_for_status()

    measured_latencies_ms: list[float] = []

    for _ in range(samples):
        start_ns = time.perf_counter_ns()

        response = STATE_HTTP_CLIENT.get(url)
        response.raise_for_status()

        end_ns = time.perf_counter_ns()

        measured_latencies_ms.append(
            (end_ns - start_ns) / 1_000_000
        )

    return median(measured_latencies_ms)

def build_routing_context(
    *,
    minimum_quality_score: float,
    privacy_required: bool = False,
    cloud_health_url: str = DEFAULT_CLOUD_HEALTH_URL,
    cpu_sample_interval_s: float = DEFAULT_CPU_SAMPLE_INTERVAL_S,
    rtt_samples: int = DEFAULT_RTT_SAMPLES,
    rtt_warmup_requests: int = DEFAULT_RTT_WARMUP_REQUESTS,
) -> RoutingContext:
    """Build a routing context from live system measurements."""

    local_load_ratio = measure_local_load_ratio(
        sample_interval_s=cpu_sample_interval_s,
    )

    estimated_cloud_rtt_ms = measure_endpoint_rtt_ms(
        url=cloud_health_url,
        samples=rtt_samples,
        warmup_requests=rtt_warmup_requests,
    )

    return RoutingContext(
        estimated_cloud_rtt_ms=estimated_cloud_rtt_ms,
        local_load_ratio=local_load_ratio,
        minimum_quality_score=minimum_quality_score,
        privacy_required=privacy_required,
    )