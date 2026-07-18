"""Pydantic schemas shared by backends, benchmarks, and future API layers."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

EndpointName = Literal["local", "cloud"]


class InferenceRequest(BaseModel):
    """A model-independent inference request."""

    model_config = ConfigDict(extra="forbid")

    request_id: str = Field(min_length=1)
    prompt: str = Field(min_length=1)
    task_type: str = Field(default="smoke", min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)


class InferenceResponse(BaseModel):
    """A normalized response returned by an inference backend."""

    model_config = ConfigDict(extra="forbid")

    request_id: str
    endpoint: EndpointName
    output_text: str
    quality_score: float = Field(ge=0.0, le=1.0)
    configured_processing_delay_ms: float = Field(ge=0.0)
    configured_rtt_ms: float = Field(ge=0.0)
    server_processing_ms: float | None = Field(default=None, ge=0.0)
    success: bool = True
    error_type: str | None = None


class SystemSnapshot(BaseModel):
    """Client-side process and system metrics at one point in time."""

    model_config = ConfigDict(extra="forbid")

    process_cpu_percent: float = Field(ge=0.0)
    process_rss_mb: float = Field(ge=0.0)
    system_cpu_percent: float = Field(ge=0.0)
    system_memory_percent: float = Field(ge=0.0, le=100.0)


class BenchmarkRecord(BaseModel):
    """One endpoint execution record written to the JSONL result file."""

    model_config = ConfigDict(extra="forbid")

    experiment_id: str
    run_id: str
    request_id: str
    timestamp: datetime
    split: str = "smoke"
    policy_name: str = "paired_profile"
    selected_endpoint: EndpointName
    decision_reason: str
    task_type: str
    prompt_length: int = Field(ge=0)
    estimated_complexity: str | None = None

    client_process_cpu_before: float = Field(ge=0.0)
    client_process_cpu_after: float = Field(ge=0.0)
    client_process_rss_before_mb: float = Field(ge=0.0)
    client_process_rss_after_mb: float = Field(ge=0.0)
    system_cpu_before: float = Field(ge=0.0)
    system_cpu_after: float = Field(ge=0.0)
    system_memory_before: float = Field(ge=0.0, le=100.0)
    system_memory_after: float = Field(ge=0.0, le=100.0)

    network_mode: str
    configured_rtt_ms: float = Field(ge=0.0)
    measured_rtt_ms: float | None = Field(default=None, ge=0.0)

    request_start_time: datetime
    request_end_time: datetime
    latency_ms: float = Field(ge=0.0)
    time_to_first_token_ms: float | None = Field(default=None, ge=0.0)
    response_length: int = Field(ge=0)
    quality_score: float = Field(ge=0.0, le=1.0)
    success: bool
    error_type: str | None = None
    request_payload_bytes: int = Field(ge=0)
    response_payload_bytes: int = Field(ge=0)

    endpoint_process_cpu: float | None = Field(default=None, ge=0.0)
    endpoint_process_rss_mb: float | None = Field(default=None, ge=0.0)
    endpoint_peak_rss_mb: float | None = Field(default=None, ge=0.0)
    gpu_utilization_before: float | None = Field(default=None, ge=0.0)
    gpu_utilization_after: float | None = Field(default=None, ge=0.0)

    model_name: str
    model_quantization: str | None = None
    seed: int
    git_commit: str | None = None
    config_path: str | None = None
