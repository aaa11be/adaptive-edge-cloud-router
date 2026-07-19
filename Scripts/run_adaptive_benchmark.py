from edge_cloud_router.evaluation.baseline_benchmark import (
    run_adaptive_benchmark,
    save_results_jsonl,
    save_summary_json,
    summarize_adaptive_results,
)
from edge_cloud_router.schemas import RoutingContext


def build_contexts(repetitions: int) -> list[RoutingContext]:
    scenario_contexts = [
        # 일반적인 저품질 요구: Local 선택
        RoutingContext(
            estimated_cloud_rtt_ms=150.0,
            local_load_ratio=0.2,
            minimum_quality_score=0.5,
            privacy_required=False,
        ),
        # 높은 품질 요구: Cloud 선택
        RoutingContext(
            estimated_cloud_rtt_ms=30.0,
            local_load_ratio=0.2,
            minimum_quality_score=0.8,
            privacy_required=False,
        ),
        # Local 고부하 + 낮은 Cloud RTT: Cloud 선택
        RoutingContext(
            estimated_cloud_rtt_ms=30.0,
            local_load_ratio=0.9,
            minimum_quality_score=0.5,
            privacy_required=False,
        ),
        # 개인정보 보호 요청: Local 선택
        RoutingContext(
            estimated_cloud_rtt_ms=10.0,
            local_load_ratio=1.0,
            minimum_quality_score=0.9,
            privacy_required=True,
        ),
    ]

    return scenario_contexts * repetitions


def main() -> None:
    contexts = build_contexts(repetitions=10)

    warmup_contexts = [
        RoutingContext(
            estimated_cloud_rtt_ms=150.0,
            local_load_ratio=0.2,
            minimum_quality_score=0.5,
        ),
        RoutingContext(
            estimated_cloud_rtt_ms=30.0,
            local_load_ratio=0.2,
            minimum_quality_score=0.8,
        ),
    ]

    results = run_adaptive_benchmark(
        contexts=contexts,
        warmup_contexts=warmup_contexts,
    )

    summary = summarize_adaptive_results(results)

    save_results_jsonl(
        results,
        "results/adaptive_balanced.jsonl",
    )
    save_summary_json(
        summary,
        "results/adaptive_balanced_summary.json",
    )

    print("measured requests:", len(results))
    print("summary:", summary)


if __name__ == "__main__":
    main()