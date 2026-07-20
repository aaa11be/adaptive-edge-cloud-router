from __future__ import annotations

from dataclasses import dataclass


DEFAULT_PROBE_CACHE_TTL_S = 10.0


@dataclass(slots=True)
class CloudProbeCache:

    ttl_s: float = DEFAULT_PROBE_CACHE_TTL_S
    available: bool | None = None
    latency_ms: float | None = None
    measured_at_s: float | None = None

    def __post_init__(self) -> None:
        if self.ttl_s <= 0.0:
            raise ValueError(
                "ttl_s must be greater than 0"
            )

        if self.latency_ms is not None:
            if self.latency_ms < 0.0:
                raise ValueError(
                    "latency_ms must not be negative"
                )

        if self.measured_at_s is not None:
            if self.measured_at_s < 0.0:
                raise ValueError(
                    "measured_at_s must not be negative"
                )

    def has_fresh_result(
        self,
        current_time_s: float,
    ) -> bool:

        if current_time_s < 0.0:
            raise ValueError(
                "current_time_s must not be negative"
            )

        if self.available is None:
            return False

        if self.measured_at_s is None:
            return False

        elapsed_s = current_time_s - self.measured_at_s

        if elapsed_s < 0.0:
            return False

        return elapsed_s < self.ttl_s

    def store_success(
        self,
        *,
        latency_ms: float,
        measured_at_s: float,
    ) -> None:

        if latency_ms < 0.0:
            raise ValueError(
                "latency_ms must not be negative"
            )

        if measured_at_s < 0.0:
            raise ValueError(
                "measured_at_s must not be negative"
            )

        self.available = True
        self.latency_ms = latency_ms
        self.measured_at_s = measured_at_s

    def store_failure(
        self,
        *,
        measured_at_s: float,
    ) -> None:

        if measured_at_s < 0.0:
            raise ValueError(
                "measured_at_s must not be negative"
            )

        self.available = False
        self.latency_ms = None
        self.measured_at_s = measured_at_s