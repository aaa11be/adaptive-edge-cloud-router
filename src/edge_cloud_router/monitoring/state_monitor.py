import time
from statistics import median

import httpx
import psutil

from edge_cloud_router.schemas import RoutingContext


DEFAULT_CPU_SAMPLE_INTERVAL_S = 0.1

# Initial end-to-end latency estimates measured from the
# real-model benchmark. These will later be updated from
# recent inference observations.
DEFAULT_LOCAL_LATENCY_ESTIMATE_MS = 3870.0
DEFAULT_CLOUD_LATENCY_ESTIMATE_MS = 1144.0

# A cloud probe performs a minimal remote inference request.
# Keep the count low to avoid unnecessary latency and cost.
DEFAULT_PROBE_SAMPLES = 1
DEFAULT_PROBE_WARMUP_REQUESTS = 0
DEFAULT_HTTP_TIMEOUT_S = 10.0

DEFAULT_CLOUD_PROBE_URL = (
    "http://127.0.0.1:8001/remote-health"
)


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


def measure_endpoint_latency_ms(
    url: str,
    samples: int = DEFAULT_PROBE_SAMPLES,
    warmup_requests: int = (
        DEFAULT_PROBE_WARMUP_REQUESTS
    ),
) -> float:
    """Measure median end-to-end latency of an HTTP endpoint."""

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
    estimated_local_latency_ms: float = (
        DEFAULT_LOCAL_LATENCY_ESTIMATE_MS
    ),
    estimated_cloud_latency_ms: float = (
        DEFAULT_CLOUD_LATENCY_ESTIMATE_MS
    ),
    cloud_probe_url: str = DEFAULT_CLOUD_PROBE_URL,
    cpu_sample_interval_s: float = (
        DEFAULT_CPU_SAMPLE_INTERVAL_S
    ),
    probe_samples: int = DEFAULT_PROBE_SAMPLES,
    probe_warmup_requests: int = (
        DEFAULT_PROBE_WARMUP_REQUESTS
    ),
) -> RoutingContext:
    """Build a routing context from estimates and live state."""

    local_load_ratio = measure_local_load_ratio(
        sample_interval_s=cpu_sample_interval_s,
    )

    cloud_available = True
    cloud_probe_latency_ms: float | None

    try:
        cloud_probe_latency_ms = (
            measure_endpoint_latency_ms(
                url=cloud_probe_url,
                samples=probe_samples,
                warmup_requests=probe_warmup_requests,
            )
        )
    except httpx.HTTPError:
        cloud_available = False
        cloud_probe_latency_ms = None

    return RoutingContext(
        estimated_local_latency_ms=(
            estimated_local_latency_ms
        ),
        estimated_cloud_latency_ms=(
            estimated_cloud_latency_ms
        ),
        local_load_ratio=local_load_ratio,
        minimum_quality_score=minimum_quality_score,
        privacy_required=privacy_required,
        cloud_available=cloud_available,
        cloud_probe_latency_ms=cloud_probe_latency_ms,
    )