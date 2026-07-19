from edge_cloud_router.evaluation.baseline_benchmark import summarize_results


def test_summarize_results() -> None:
    results = [
        {"end_to_end_latency_ms": 10.0},
        {"end_to_end_latency_ms": 20.0},
        {"end_to_end_latency_ms": 30.0},
        {"end_to_end_latency_ms": 40.0},
        {"end_to_end_latency_ms": 50.0},
    ]

    summary = summarize_results(results)

    assert summary["mean_latency_ms"] == 30.0
    assert summary["p50_latency_ms"] == 30.0
    assert summary["p95_latency_ms"] == 50.0