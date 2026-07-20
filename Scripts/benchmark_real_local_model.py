from edge_cloud_router.evaluation.baseline_benchmark import (
    run_single_request,
    save_results_jsonl,
    save_summary_json,
    summarize_results,
)


MEASURED_REQUESTS = 5


def main() -> None:
    print("running first request...")

    first_request_result = run_single_request(
        strategy="always_local",
        request_index=1,
    )

    print(
        "first request latency:",
        f"{first_request_result['end_to_end_latency_ms']:.3f} ms",
    )
    print(
        "first server processing:",
        f"{first_request_result['server_processing_ms']:.3f} ms",
    )

    print()
    print(
        f"running {MEASURED_REQUESTS} repeated requests..."
    )

    repeated_results = [
        run_single_request(
            strategy="always_local",
            request_index=request_index,
        )
        for request_index in range(
            2,
            MEASURED_REQUESTS + 2,
        )
    ]

    repeated_summary = summarize_results(
        repeated_results,
    )

    save_results_jsonl(
        [first_request_result],
        "results/real_local_first_request.jsonl",
    )
    save_results_jsonl(
        repeated_results,
        "results/real_local_repeated.jsonl",
    )
    save_summary_json(
        repeated_summary,
        "results/real_local_repeated_summary.json",
    )

    print()
    print("repeated summary:")
    print(repeated_summary)


if __name__ == "__main__":
    main()