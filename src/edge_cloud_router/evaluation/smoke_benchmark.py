"""Paired deterministic smoke benchmark for the Phase 1 pipeline."""

from __future__ import annotations

import argparse
import json
import random
import time
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Sequence

from edge_cloud_router.inference.mock_backend import DeterministicMockBackend
from edge_cloud_router.monitoring.request_logger import JsonlRequestLogger
from edge_cloud_router.monitoring.system_metrics import SystemMetricsCollector
from edge_cloud_router.schemas import BenchmarkRecord, InferenceRequest


@dataclass(frozen=True, slots=True)
class SmokeBenchmarkResult:
    """Summary returned to tests and CLI callers."""

    output_path: Path
    records: tuple[BenchmarkRecord, BenchmarkRecord]


def _utc_now() -> datetime:
    return datetime.now(tz=UTC)


def _payload_size_bytes(payload: object) -> int:
    serialized = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    return len(serialized.encode("utf-8"))


def _execute_backend(
    *,
    request: InferenceRequest,
    backend: DeterministicMockBackend,
    experiment_id: str,
    run_id: str,
    seed: int,
    collector: SystemMetricsCollector,
) -> BenchmarkRecord:
    before = collector.snapshot()
    start_wall = _utc_now()
    start_perf_ns = time.perf_counter_ns()

    response = backend.infer(request)

    end_perf_ns = time.perf_counter_ns()
    end_wall = _utc_now()
    after = collector.snapshot()

    request_payload = request.model_dump(mode="json")
    response_payload = response.model_dump(mode="json")

    return BenchmarkRecord(
        experiment_id=experiment_id,
        run_id=run_id,
        request_id=request.request_id,
        timestamp=start_wall,
        selected_endpoint=backend.endpoint,
        decision_reason="paired Phase 1 pipeline validation",
        task_type=request.task_type,
        prompt_length=len(request.prompt),
        client_process_cpu_before=before.process_cpu_percent,
        client_process_cpu_after=after.process_cpu_percent,
        client_process_rss_before_mb=before.process_rss_mb,
        client_process_rss_after_mb=after.process_rss_mb,
        system_cpu_before=before.system_cpu_percent,
        system_cpu_after=after.system_cpu_percent,
        system_memory_before=before.system_memory_percent,
        system_memory_after=after.system_memory_percent,
        network_mode="configured_delay",
        configured_rtt_ms=backend.configured_rtt_ms,
        request_start_time=start_wall,
        request_end_time=end_wall,
        latency_ms=(end_perf_ns - start_perf_ns) / 1_000_000,
        response_length=len(response.output_text),
        quality_score=response.quality_score,
        success=response.success,
        error_type=response.error_type,
        request_payload_bytes=_payload_size_bytes(request_payload),
        response_payload_bytes=_payload_size_bytes(response_payload),
        model_name=backend.model_name,
        seed=seed,
    )


def run_smoke_benchmark(
    *,
    output_path: str | Path,
    prompt: str,
    seed: int = 42,
    local_delay_ms: float = 20.0,
    cloud_delay_ms: float = 80.0,
    cloud_rtt_ms: float = 40.0,
    local_quality: float = 0.60,
    cloud_quality: float = 0.90,
) -> SmokeBenchmarkResult:
    """Run one request against both mock backends and write two JSONL records."""

    if not prompt.strip():
        raise ValueError("prompt must not be blank")

    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.unlink(missing_ok=True)

    experiment_id = "phase1-smoke"
    run_id = str(uuid.uuid4())
    request = InferenceRequest(
        request_id=str(uuid.uuid4()),
        prompt=prompt,
        task_type="smoke",
    )

    backends = [
        DeterministicMockBackend(
            endpoint="local",
            processing_delay_ms=local_delay_ms,
            configured_rtt_ms=0.0,
            quality_score=local_quality,
            model_name="deterministic-local-mock-v1",
        ),
        DeterministicMockBackend(
            endpoint="cloud",
            processing_delay_ms=cloud_delay_ms,
            configured_rtt_ms=cloud_rtt_ms,
            quality_score=cloud_quality,
            model_name="deterministic-cloud-mock-v1",
        ),
    ]
    random.Random(seed).shuffle(backends)

    collector = SystemMetricsCollector()
    collector.warm_up()
    logger = JsonlRequestLogger(destination)

    records_by_endpoint: dict[str, BenchmarkRecord] = {}
    for backend in backends:
        record = _execute_backend(
            request=request,
            backend=backend,
            experiment_id=experiment_id,
            run_id=run_id,
            seed=seed,
            collector=collector,
        )
        logger.append(record)
        records_by_endpoint[backend.endpoint] = record

    records = (records_by_endpoint["local"], records_by_endpoint["cloud"])
    return SmokeBenchmarkResult(output_path=destination, records=records)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="results/smoke.jsonl")
    parser.add_argument(
        "--prompt",
        default="Classify this request for the edge-cloud routing smoke test.",
    )
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--local-delay-ms", type=float, default=20.0)
    parser.add_argument("--cloud-delay-ms", type=float, default=80.0)
    parser.add_argument("--cloud-rtt-ms", type=float, default=40.0)
    parser.add_argument("--local-quality", type=float, default=0.60)
    parser.add_argument("--cloud-quality", type=float, default=0.90)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = run_smoke_benchmark(
        output_path=args.output,
        prompt=args.prompt,
        seed=args.seed,
        local_delay_ms=args.local_delay_ms,
        cloud_delay_ms=args.cloud_delay_ms,
        cloud_rtt_ms=args.cloud_rtt_ms,
        local_quality=args.local_quality,
        cloud_quality=args.cloud_quality,
    )

    local, cloud = result.records
    print(f"Wrote 2 records to {result.output_path}")
    print(
        "local: "
        f"latency={local.latency_ms:.2f} ms, quality={local.quality_score:.2f}, "
        f"rss_after={local.client_process_rss_after_mb:.2f} MiB"
    )
    print(
        "cloud: "
        f"latency={cloud.latency_ms:.2f} ms, quality={cloud.quality_score:.2f}, "
        f"rss_after={cloud.client_process_rss_after_mb:.2f} MiB"
    )
    print("Interpretation: pipeline validation only; these are configured mock conditions.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
