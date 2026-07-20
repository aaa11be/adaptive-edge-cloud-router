from __future__ import annotations

from dataclasses import dataclass

from edge_cloud_router.schemas import EndpointName


DEFAULT_LOCAL_LATENCY_MS = 3870.0
DEFAULT_CLOUD_LATENCY_MS = 1144.0
DEFAULT_SMOOTHING_FACTOR = 0.3


@dataclass(slots=True)
class LatencyEstimator:
    """Track local and cloud end-to-end latency using EWMA."""

    local_latency_ms: float = DEFAULT_LOCAL_LATENCY_MS
    cloud_latency_ms: float = DEFAULT_CLOUD_LATENCY_MS
    smoothing_factor: float = DEFAULT_SMOOTHING_FACTOR

    def __post_init__(self) -> None:
        if self.local_latency_ms < 0.0:
            raise ValueError(
                "local_latency_ms must not be negative"
            )

        if self.cloud_latency_ms < 0.0:
            raise ValueError(
                "cloud_latency_ms must not be negative"
            )

        if not 0.0 < self.smoothing_factor <= 1.0:
            raise ValueError(
                "smoothing_factor must be greater than 0 "
                "and less than or equal to 1"
            )

    def get_estimate(
        self,
        endpoint: EndpointName,
    ) -> float:
        """Return the current estimate for one endpoint."""

        if endpoint == "local":
            return self.local_latency_ms

        return self.cloud_latency_ms

    def update(
        self,
        endpoint: EndpointName,
        observed_latency_ms: float,
    ) -> float:
        """Update one endpoint estimate using an observation."""

        if observed_latency_ms < 0.0:
            raise ValueError(
                "observed_latency_ms must not be negative"
            )

        previous_estimate = self.get_estimate(endpoint)

        updated_estimate = (
            self.smoothing_factor * observed_latency_ms
            + (1.0 - self.smoothing_factor)
            * previous_estimate
        )

        if endpoint == "local":
            self.local_latency_ms = updated_estimate
        else:
            self.cloud_latency_ms = updated_estimate

        return updated_estimate