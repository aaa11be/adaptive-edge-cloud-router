import json
from pathlib import Path
import pytest

from edge_cloud_router.evaluation import baseline_benchmark
from edge_cloud_router.evaluation.baseline_benchmark import (
    save_results_jsonl,
    save_summary_json,
    summarize_adaptive_results,
    summarize_results,
)
from types import SimpleNamespace

from edge_cloud_router.schemas import RoutingContext

def test_summarize_results() -> None:
    results = [
        {
            "endpoint": "local",
            "end_to_end_latency_ms": 10.0,
            "server_processing_ms": 8.0,
            "quality_score": 0.6,
            "success": True,
        },
        {
            "endpoint": "local",
            "end_to_end_latency_ms": 20.0,
            "server_processing_ms": 18.0,
            "quality_score": 0.6,
            "success": True,
        },
        {
            "endpoint": "local",
            "end_to_end_latency_ms": 30.0,
            "server_processing_ms": 28.0,
            "quality_score": 0.6,
            "success": True,
        },
        {
            "endpoint": "cloud",
            "end_to_end_latency_ms": 40.0,
            "server_processing_ms": 38.0,
            "quality_score": 0.6,
            "success": True,
        },
        {
            "endpoint": "cloud",
            "end_to_end_latency_ms": 50.0,
            "server_processing_ms": 48.0,
            "quality_score": 0.6,
            "success": False,
        },
    ]

    summary = summarize_results(results)

    assert summary["mean_latency_ms"] == 30.0
    assert summary["p50_latency_ms"] == 30.0
    assert summary["p95_latency_ms"] == 50.0
    assert summary["mean_server_processing_ms"] == 28.0
    assert summary["mean_non_inference_overhead_ms"] == 2.0
    assert summary["mean_quality_score"] == 0.6
    assert summary["success_rate"] == 0.8
    assert summary["local_selection_rate"] == 0.6
    assert summary["cloud_selection_rate"] == 0.4


def test_save_results_jsonl(tmp_path: Path) -> None:
    results = [
        {
            "request_id": "request-001",
            "end_to_end_latency_ms": 10.0,
        },
        {
            "request_id": "request-002",
            "end_to_end_latency_ms": 20.0,
        },
    ]

    output_path = tmp_path / "nested" / "results.jsonl"

    save_results_jsonl(results, str(output_path))

    lines = output_path.read_text(
        encoding="utf-8",
    ).splitlines()

    saved_results = [
        json.loads(line)
        for line in lines
    ]

    assert saved_results == results

def test_run_benchmark_excludes_warmup_requests(
    monkeypatch,
) -> None:
    called_request_indices: list[int] = []

    def fake_run_single_request(
        strategy: str,
        request_index: int,
    ) -> dict:
        called_request_indices.append(request_index)

        return {
            "request_id": f"{strategy}-{request_index:03d}",
        }

    monkeypatch.setattr(
        baseline_benchmark,
        "run_single_request",
        fake_run_single_request,
    )

    results = baseline_benchmark.run_benchmark(
        strategy="always_local",
        num_requests=3,
        warmup_requests=2,
    )

    assert called_request_indices == [1, 2, 1, 2, 3]
    assert len(results) == 3
    assert [result["request_id"] for result in results] == [
        "always_local-001",
        "always_local-002",
        "always_local-003",
    ]

def test_save_summary_json(tmp_path: Path) -> None:
    summary = {
        "mean_latency_ms": 22.1,
        "p50_latency_ms": 22.0,
        "p95_latency_ms": 22.7,
    }

    output_path = tmp_path / "nested" / "summary.json"

    save_summary_json(
        summary,
        str(output_path),
    )

    saved_summary = json.loads(
        output_path.read_text(encoding="utf-8"),
    )

    assert saved_summary == summary

def test_summarize_results_rejects_empty_results() -> None:
    with pytest.raises(
        ValueError,
        match="results must not be empty",
    ):
        summarize_results([])

def test_run_single_adaptive_request_records_context(
    monkeypatch,
) -> None:
    context = RoutingContext(
        estimated_cloud_rtt_ms=30.0,
        local_load_ratio=0.2,
        minimum_quality_score=0.8,
        privacy_required=False,
    )

    def fake_route_adaptive_inference(
        sent_context: RoutingContext,
        request,
    ):
        assert sent_context == context
        assert request.request_id == "adaptive-001"

        return SimpleNamespace(
            request_id=request.request_id,
            endpoint="cloud",
            server_processing_ms=80.0,
            quality_score=0.9,
            success=True,
        )

    monkeypatch.setattr(
        baseline_benchmark,
        "route_adaptive_inference",
        fake_route_adaptive_inference,
    )

    result = baseline_benchmark.run_single_adaptive_request(
        context,
        request_index=1,
    )

    assert result["request_id"] == "adaptive-001"
    assert result["strategy"] == "adaptive"
    assert result["endpoint"] == "cloud"
    assert result["routing_context"] == {
        "estimated_cloud_rtt_ms": 30.0,
        "local_load_ratio": 0.2,
        "minimum_quality_score": 0.8,
        "privacy_required": False,
    }
    assert result["end_to_end_latency_ms"] >= 0.0

def test_run_adaptive_benchmark_uses_each_context(
    monkeypatch,
) -> None:
    contexts = [
        RoutingContext(
            estimated_cloud_rtt_ms=20.0,
            local_load_ratio=0.2,
            minimum_quality_score=0.5,
        ),
        RoutingContext(
            estimated_cloud_rtt_ms=30.0,
            local_load_ratio=0.9,
            minimum_quality_score=0.5,
        ),
        RoutingContext(
            estimated_cloud_rtt_ms=40.0,
            local_load_ratio=0.2,
            minimum_quality_score=0.8,
        ),
    ]

    called_contexts: list[RoutingContext] = []
    called_indices: list[int] = []

    def fake_run_single_adaptive_request(
        context: RoutingContext,
        request_index: int,
    ) -> dict:
        called_contexts.append(context)
        called_indices.append(request_index)

        return {
            "request_id": f"adaptive-{request_index:03d}",
        }

    monkeypatch.setattr(
        baseline_benchmark,
        "run_single_adaptive_request",
        fake_run_single_adaptive_request,
    )

    results = baseline_benchmark.run_adaptive_benchmark(
        contexts,
    )

    assert called_contexts == contexts
    assert called_indices == [1, 2, 3]
    assert [result["request_id"] for result in results] == [
        "adaptive-001",
        "adaptive-002",
        "adaptive-003",
    ]

def test_run_adaptive_benchmark_excludes_warmup_contexts(
    monkeypatch,
) -> None:
    local_context = RoutingContext(
        estimated_cloud_rtt_ms=150.0,
        local_load_ratio=0.2,
        minimum_quality_score=0.5,
    )

    cloud_context = RoutingContext(
        estimated_cloud_rtt_ms=30.0,
        local_load_ratio=0.2,
        minimum_quality_score=0.8,
    )

    measured_contexts = [
        local_context,
        cloud_context,
        local_context,
    ]

    called_contexts: list[RoutingContext] = []
    called_indices: list[int] = []

    def fake_run_single_adaptive_request(
        context: RoutingContext,
        request_index: int,
    ) -> dict:
        called_contexts.append(context)
        called_indices.append(request_index)

        return {
            "request_id": f"adaptive-{request_index:03d}",
        }

    monkeypatch.setattr(
        baseline_benchmark,
        "run_single_adaptive_request",
        fake_run_single_adaptive_request,
    )

    results = baseline_benchmark.run_adaptive_benchmark(
        contexts=measured_contexts,
        warmup_contexts=[
            local_context,
            cloud_context,
        ],
    )

    assert called_contexts == [
        local_context,
        cloud_context,
        local_context,
        cloud_context,
        local_context,
    ]
    assert called_indices == [1, 2, 1, 2, 3]
    assert len(results) == 3

def test_summarize_adaptive_results() -> None:
    results = [
        {
            "endpoint": "local",
            "end_to_end_latency_ms": 22.0,
            "server_processing_ms": 20.0,
            "quality_score": 0.6,
            "success": True,
            "routing_context": {
                "minimum_quality_score": 0.5,
                "privacy_required": False,
            },
        },
        {
            "endpoint": "cloud",
            "end_to_end_latency_ms": 82.0,
            "server_processing_ms": 80.0,
            "quality_score": 0.9,
            "success": True,
            "routing_context": {
                "minimum_quality_score": 0.8,
                "privacy_required": False,
            },
        },
        {
            "endpoint": "local",
            "end_to_end_latency_ms": 22.0,
            "server_processing_ms": 20.0,
            "quality_score": 0.6,
            "success": True,
            "routing_context": {
                "minimum_quality_score": 0.9,
                "privacy_required": True,
            },
        },
    ]

    summary = summarize_adaptive_results(results)

    assert summary["quality_satisfied_count"] == 2
    assert summary[
        "quality_requirement_satisfaction_rate"
    ] == pytest.approx(2 / 3)
    assert summary["privacy_required_count"] == 1
    assert summary["privacy_violation_count"] == 0
    assert summary["privacy_violation_rate"] == 0.0

def test_run_single_contextual_fixed_request_records_context(
    monkeypatch,
) -> None:
    context = RoutingContext(
        estimated_cloud_rtt_ms=30.0,
        local_load_ratio=0.9,
        minimum_quality_score=0.8,
        privacy_required=False,
    )

    def fake_route_inference(
        strategy: str,
        request,
    ):
        assert strategy == "always_local"
        assert request.request_id == "always_local-001"

        return SimpleNamespace(
            request_id=request.request_id,
            endpoint="local",
            server_processing_ms=20.0,
            quality_score=0.6,
            success=True,
        )

    monkeypatch.setattr(
        baseline_benchmark,
        "route_inference",
        fake_route_inference,
    )

    result = (
        baseline_benchmark
        .run_single_contextual_fixed_request(
            strategy="always_local",
            context=context,
            request_index=1,
        )
    )

    assert result["request_id"] == "always_local-001"
    assert result["strategy"] == "always_local"
    assert result["endpoint"] == "local"
    assert result["routing_context"] == {
        "estimated_cloud_rtt_ms": 30.0,
        "local_load_ratio": 0.9,
        "minimum_quality_score": 0.8,
        "privacy_required": False,
    }