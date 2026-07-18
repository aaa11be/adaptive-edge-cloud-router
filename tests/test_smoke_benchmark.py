from __future__ import annotations

import json
from pathlib import Path

import pytest

from edge_cloud_router.evaluation.smoke_benchmark import run_smoke_benchmark
from edge_cloud_router.inference.mock_backend import DeterministicMockBackend
from edge_cloud_router.schemas import BenchmarkRecord, InferenceRequest


def test_mock_backend_output_is_deterministic() -> None:
    backend = DeterministicMockBackend(
        endpoint="local",
        processing_delay_ms=0.0,
        quality_score=0.5,
    )
    request = InferenceRequest(request_id="request-1", prompt="same input")

    first = backend.infer(request)
    second = backend.infer(request)

    assert first.output_text == second.output_text
    assert first.request_id == second.request_id


def test_smoke_benchmark_writes_paired_records(tmp_path: Path) -> None:
    output = tmp_path / "smoke.jsonl"

    result = run_smoke_benchmark(
        output_path=output,
        prompt="paired smoke test",
        seed=7,
        local_delay_ms=2.0,
        cloud_delay_ms=20.0,
        cloud_rtt_ms=10.0,
        local_quality=0.4,
        cloud_quality=0.8,
    )

    assert result.output_path == output
    lines = output.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2

    records = [BenchmarkRecord.model_validate(json.loads(line)) for line in lines]
    by_endpoint = {record.selected_endpoint: record for record in records}

    assert set(by_endpoint) == {"local", "cloud"}
    assert by_endpoint["local"].request_id == by_endpoint["cloud"].request_id
    assert by_endpoint["local"].run_id == by_endpoint["cloud"].run_id
    assert by_endpoint["local"].quality_score == pytest.approx(0.4)
    assert by_endpoint["cloud"].quality_score == pytest.approx(0.8)
    assert by_endpoint["local"].configured_rtt_ms == pytest.approx(0.0)
    assert by_endpoint["cloud"].configured_rtt_ms == pytest.approx(10.0)
    assert by_endpoint["cloud"].latency_ms > by_endpoint["local"].latency_ms
    assert all(record.success for record in records)
    assert all(record.time_to_first_token_ms is None for record in records)
