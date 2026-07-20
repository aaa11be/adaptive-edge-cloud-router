from edge_cloud_router.evaluation.baseline_benchmark import (
    run_benchmark,
    save_results_jsonl,
    save_summary_json,
    summarize_results,
)


MEASURED_REQUESTS = 5
WARMUP_REQUESTS = 1


def run_and_save(
    *,
    strategy: str,
    output_prefix: str,
) -> dict[str, float | int]:
    results = run_benchmark(
        strategy=strategy,
        num_requests=MEASURED_REQUESTS,
        warmup_requests=WARMUP_REQUESTS,
    )

    summary = summarize_results(results)

    save_results_jsonl(
        results,
        f"results/{output_prefix}.jsonl",
    )
    save_summary_json(
        summary,
        f"results/{output_prefix}_summary.json",
    )

    return summary


def main() -> None:
    print("benchmarking real local model...")

    local_summary = run_and_save(
        strategy="always_local",
        output_prefix="real_model_local",
    )

    print("benchmarking real cloud model...")

    cloud_summary = run_and_save(
        strategy="always_cloud",
        output_prefix="real_model_cloud",
    )

    print()
    print("requests per endpoint:", MEASURED_REQUESTS)
    print("local:", local_summary)
    print("cloud:", cloud_summary)


if __name__ == "__main__":
    main()