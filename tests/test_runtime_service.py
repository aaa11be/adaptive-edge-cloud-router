from types import SimpleNamespace

from edge_cloud_router.routing import runtime_service
from edge_cloud_router.schemas import (
    InferenceRequest,
    RoutingContext,
)


def test_route_runtime_adaptive_inference_uses_measured_context(
    monkeypatch,
) -> None:
    measured_context = RoutingContext(
        estimated_local_latency_ms=2500.0,
        estimated_cloud_latency_ms=1100.0,
        local_load_ratio=0.73,
        minimum_quality_score=0.8,
        privacy_required=False,
        cloud_available=True,
        cloud_probe_latency_ms=424.5,
    )

    received_build_arguments: list[dict] = []
    received_route_arguments: list[tuple] = []

    def fake_build_routing_context(
        **kwargs,
    ) -> RoutingContext:
        received_build_arguments.append(kwargs)
        return measured_context

    def fake_route_adaptive_inference(
        context: RoutingContext,
        request: InferenceRequest,
    ):
        received_route_arguments.append(
            (
                context,
                request,
            )
        )

        return SimpleNamespace(
            request_id=request.request_id,
            endpoint="cloud",
            server_processing_ms=80.0,
            quality_score=0.9,
            success=True,
        )

    monkeypatch.setattr(
        runtime_service,
        "build_routing_context",
        fake_build_routing_context,
    )
    monkeypatch.setattr(
        runtime_service,
        "route_adaptive_inference",
        fake_route_adaptive_inference,
    )

    request = InferenceRequest(
        request_id="runtime-adaptive-001",
        prompt="What is edge AI?",
        task_type="smoke",
    )

    context, response = (
        runtime_service
        .route_runtime_adaptive_inference(
            request=request,
            minimum_quality_score=0.8,
            privacy_required=False,
            estimated_local_latency_ms=2500.0,
            estimated_cloud_latency_ms=1100.0,
            cloud_probe_url=(
                "http://cloud.example/remote-health"
            ),
            cpu_sample_interval_s=0.25,
            probe_samples=5,
            probe_warmup_requests=2,
        )
    )

    assert received_build_arguments == [
        {
            "minimum_quality_score": 0.8,
            "privacy_required": False,
            "estimated_local_latency_ms": 2500.0,
            "estimated_cloud_latency_ms": 1100.0,
            "cloud_probe_url": (
                "http://cloud.example/remote-health"
            ),
            "cpu_sample_interval_s": 0.25,
            "probe_samples": 5,
            "probe_warmup_requests": 2,
        }
    ]

    assert received_route_arguments == [
        (
            measured_context,
            request,
        )
    ]

    assert context == measured_context
    assert response.endpoint == "cloud"