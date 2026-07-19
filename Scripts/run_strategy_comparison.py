from edge_cloud_router.evaluation.baseline_benchmark import (
    run_adaptive_benchmark,
    run_contextual_fixed_benchmark,
    save_results_jsonl,
    save_summary_json,
    summarize_adaptive_results,
)
from edge_cloud_router.schemas import RoutingContext


def build_contexts(
    repetitions: int,
) -> list[RoutingContext]:
    scenario_contexts = [
        # 일반 요청: Local 품질로 충분
        RoutingContext(
            estimated_cloud_rtt_ms=150.0,
            local_load_ratio=0.2,
            minimum_quality_score=0.5,
            privacy_required=False,
        ),
        # 높은 품질 요구
        RoutingContext(
            estimated_cloud_rtt_ms=30.0,
            local_load_ratio=0.2,
            minimum_quality_score=0.8,
            privacy_required=False,
        ),
        # Local 고부하, Cloud RTT 양호
        RoutingContext(
            estimated_cloud_rtt_ms=30.0,
            local_load_ratio=0.9,
            minimum_quality_score=0.5,
            privacy_required=False,
        ),
        # 개인정보 보호 요청
        RoutingContext(
            estimated_cloud_rtt_ms=10.0,
            local_load_ratio=1.0,
            minimum_quality_score=0.9,
            privacy_required=True,
        ),
    ]

    return scenario_contexts * repetitions


def save_strategy_results(
    strategy_name: str,
    results: list[dict],
) -> dict[str, float | int]:
    summary = summarize_adaptive_results(results)

    save_results_jsonl(
        results,
        f"results/comparison_{strategy_name}.jsonl",
    )
    save_summary_json(
        summary,
        f"results/comparison_{strategy_name}_summary.json",
    )

    return summary


def main() -> None:
    contexts = build_contexts(repetitions=10)

    always_local_results = run_contextual_fixed_benchmark(
        strategy="always_local",
        contexts=contexts,
        warmup_requests=3,
    )

    always_cloud_results = run_contextual_fixed_benchmark(
        strategy="always_cloud",
        contexts=contexts,
        warmup_requests=3,
    )

    adaptive_results = run_adaptive_benchmark(
        contexts=contexts,
        warmup_contexts=[
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
        ],
    )

    always_local_summary = save_strategy_results(
        "always_local",
        always_local_results,
    )
    always_cloud_summary = save_strategy_results(
        "always_cloud",
        always_cloud_results,
    )
    adaptive_summary = save_strategy_results(
        "adaptive",
        adaptive_results,
    )

    print("requests per strategy:", len(contexts))
    print("always_local:", always_local_summary)
    print("always_cloud:", always_cloud_summary)
    print("adaptive:", adaptive_summary)


if __name__ == "__main__":
    main()