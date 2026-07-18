from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass

from edge_cloud_router.schemas import EndpointName, InferenceRequest, InferenceResponse


@dataclass(frozen=True, slots=True)
class DeterministicMockBackend:
    """Return reproducible output after a configurable deterministic delay."""

    endpoint: EndpointName
    processing_delay_ms: float
    quality_score: float
    configured_rtt_ms: float = 0.0
    model_name: str = "deterministic-mock-v1"

    def __post_init__(self) -> None:
        if self.processing_delay_ms < 0:
            raise ValueError("processing_delay_ms must be non-negative")
        if self.configured_rtt_ms < 0:
            raise ValueError("configured_rtt_ms must be non-negative")
        if not 0.0 <= self.quality_score <= 1.0:
            raise ValueError("quality_score must be between 0 and 1")

    def infer(self, request: InferenceRequest) -> InferenceResponse:
        """Execute the deterministic mock request."""

        total_delay_seconds = (self.processing_delay_ms + self.configured_rtt_ms) / 1000.0
        time.sleep(total_delay_seconds)

        digest_input = f"{request.prompt}|{request.task_type}".encode()
        digest = hashlib.sha256(digest_input).hexdigest()[:16]
        output_text = f"mock-response:{digest}"

        return InferenceResponse(
            request_id=request.request_id,
            endpoint=self.endpoint,
            output_text=output_text,
            quality_score=self.quality_score,
            configured_processing_delay_ms=self.processing_delay_ms,
            configured_rtt_ms=self.configured_rtt_ms,
        )
