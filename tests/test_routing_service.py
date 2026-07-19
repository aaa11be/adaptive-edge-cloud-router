from edge_cloud_router.routing import service
from edge_cloud_router.schemas import (
    InferenceRequest,
    RoutingContext,
)
from pytest import MonkeyPatch
from edge_cloud_router.client.http_client import (
    CLOUD_INFER_URL,
    LOCAL_INFER_URL,
)
from edge_cloud_router.routing import service
from edge_cloud_router.schemas import InferenceRequest, InferenceResponse


def test_route_inference_to_local(monkeypatch: MonkeyPatch) -> None:
    request = InferenceRequest(
        request_id="routing-service-local-001",
        prompt="What is edge AI?",
        task_type="smoke",
        metadata={},
    )

    def fake_send_inference_request(
        url: str,
        received_request: InferenceRequest,
    ) -> InferenceResponse:
        assert url == LOCAL_INFER_URL
        assert received_request == request

        return InferenceResponse(
            request_id=request.request_id,
            endpoint="local",
            output_text="mock-response:test",
            quality_score=0.60,
            configured_processing_delay_ms=20.0,
            configured_rtt_ms=0.0,
            server_processing_ms=20.1,
            success=True,
            error_type=None,
        )

    monkeypatch.setattr(
        service,
        "send_inference_request",
        fake_send_inference_request,
    )

    response = service.route_inference("always_local", request)

    assert response.endpoint == "local"
    assert response.request_id == "routing-service-local-001"

def test_route_inference_to_cloud(monkeypatch: MonkeyPatch) -> None:
    request = InferenceRequest(
        request_id="routing-service-cloud-001",
        prompt="What is edge AI?",
        task_type="smoke",
        metadata={},
    )

    def fake_send_inference_request(
        url: str,
        received_request: InferenceRequest,
    ) -> InferenceResponse:
        assert url == CLOUD_INFER_URL
        assert received_request == request

        return InferenceResponse(
            request_id=request.request_id,
            endpoint="cloud",
            output_text="mock-response:test",
            quality_score=0.90,
            configured_processing_delay_ms=80.0,
            configured_rtt_ms=0.0,
            server_processing_ms=80.1,
            success=True,
            error_type=None,
        )

    monkeypatch.setattr(
        service,
        "send_inference_request",
        fake_send_inference_request,
    )

    response = service.route_inference("always_cloud", request)

    assert response.endpoint == "cloud"
    assert response.request_id == "routing-service-cloud-001"

def test_route_adaptive_inference_calls_cloud(
    monkeypatch,
) -> None:
    request = InferenceRequest(
        request_id="adaptive-001",
        prompt="What is edge AI?",
        task_type="smoke",
        metadata={},
    )

    context = RoutingContext(
        estimated_cloud_rtt_ms=30.0,
        local_load_ratio=0.2,
        minimum_quality_score=0.8,
        privacy_required=False,
    )

    expected_response = object()

    def fake_send_inference_request(
        url: str,
        sent_request: InferenceRequest,
    ) -> object:
        assert url == service.CLOUD_INFER_URL
        assert sent_request == request

        return expected_response

    monkeypatch.setattr(
        service,
        "send_inference_request",
        fake_send_inference_request,
    )

    response = service.route_adaptive_inference(
        context,
        request,
    )

    assert response is expected_response

def test_route_adaptive_inference_keeps_private_request_local(
    monkeypatch,
) -> None:
    request = InferenceRequest(
        request_id="adaptive-private-001",
        prompt="Private information",
        task_type="smoke",
        metadata={},
    )

    context = RoutingContext(
        estimated_cloud_rtt_ms=10.0,
        local_load_ratio=1.0,
        minimum_quality_score=0.9,
        privacy_required=True,
    )

    expected_response = object()

    def fake_send_inference_request(
        url: str,
        sent_request: InferenceRequest,
    ) -> object:
        assert url == service.LOCAL_INFER_URL
        assert sent_request == request

        return expected_response

    monkeypatch.setattr(
        service,
        "send_inference_request",
        fake_send_inference_request,
    )

    response = service.route_adaptive_inference(
        context,
        request,
    )

    assert response is expected_response