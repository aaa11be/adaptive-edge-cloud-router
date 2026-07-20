from __future__ import annotations

from dataclasses import dataclass

from edge_cloud_router.schemas import EndpointName


DEFAULT_LOCAL_LATENCY_MS = 3870.0
DEFAULT_CLOUD_LATENCY_MS = 1144.0
DEFAULT_SMOOTHING_FACTOR = 0.3


@dataclass(slots=True)
class LatencyEstimator:
    """Track endpoint latency using EWMA."""

    local_latency_ms: float = DEFAULT_LOCAL_LATENCY_MS
    cloud_latency_ms: float = DEFAULT_CLOUD_LATENCY_MS
    smoothing_factor: float = DEFAULT_SMOOTHING_FACTOR
    local_observation_count: int = 0
    cloud_observation_count: int = 0

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

        if self.local_observation_count < 0:
            raise ValueError(
                "local_observation_count must not be negative"
            )

        if self.cloud_observation_count < 0:
            raise ValueError(
                "cloud_observation_count must not be negative"
            )

    def get_estimate(
        self,
        endpoint: EndpointName,
    ) -> float:
        """Return the current latency estimate."""

        if endpoint == "local":
            return self.local_latency_ms

        return self.cloud_latency_ms

    def get_observation_count(
        self,
        endpoint: EndpointName,
    ) -> int:
        """Return the successful observation count."""

        if endpoint == "local":
            return self.local_observation_count

        return self.cloud_observation_count

    def update(
        self,
        endpoint: EndpointName,
        observed_latency_ms: float,
    ) -> float:
        """Update one endpoint estimate using EWMA."""

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
            self.local_observation_count += 1
        else:
            self.cloud_latency_ms = updated_estimate
            self.cloud_observation_count += 1

        return updated_estimate