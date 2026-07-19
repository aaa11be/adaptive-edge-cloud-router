import time

from edge_cloud_router.routing.runtime_service import (
    route_runtime_adaptive_inference,
)
from edge_cloud_router.schemas import InferenceRequest


def run_scenario(
    *,
    scenario_name: str,
    request_index: int,
    minimum_quality_score: float,
    privacy_required: bool,
) -> None:
    request = InferenceRequest(
        request_id=f"live-adaptive-{request_index:03d}",
        prompt="What is edge AI?",
        task_type="smoke",
        metadata={
            "scenario": scenario_name,
        },
    )

    start_ns = time.perf_counter_ns()

    context, response = route_runtime_adaptive_inference(
        request=request,
        minimum_quality_score=minimum_quality_score,
        privacy_required=privacy_required,
    )

    end_ns = time.perf_counter_ns()

    total_runtime_ms = (
        end_ns - start_ns
    ) / 1_000_000

    print()
    print(f"scenario: {scenario_name}")
    print(f"context: {context.model_dump()}")
    print(f"selected endpoint: {response.endpoint}")
    print(f"quality score: {response.quality_score}")
    print(
        "server processing:",
        f"{response.server_processing_ms:.3f} ms",
    )
    print(
        "measurement + routing + inference:",
        f"{total_runtime_ms:.3f} ms",
    )


def main() -> None:
    run_scenario(
        scenario_name="normal",
        request_index=1,
        minimum_quality_score=0.5,
        privacy_required=False,
    )

    run_scenario(
        scenario_name="high_quality",
        request_index=2,
        minimum_quality_score=0.8,
        privacy_required=False,
    )

    run_scenario(
        scenario_name="privacy_required",
        request_index=3,
        minimum_quality_score=0.9,
        privacy_required=True,
    )


if __name__ == "__main__":
    main()