from edge_cloud_router.client.http_client import (
    CLOUD_INFER_URL,
    LOCAL_INFER_URL,
    send_inference_request,
)
from edge_cloud_router.routing.router import RoutingStrategy, select_endpoint
from edge_cloud_router.schemas import InferenceRequest, InferenceResponse


ENDPOINT_URLS = {
    "local": LOCAL_INFER_URL,
    "cloud": CLOUD_INFER_URL,
}

def route_inference(
    strategy: RoutingStrategy,
    request: InferenceRequest,
) -> InferenceResponse:
    endpoint = select_endpoint(strategy)
    url = ENDPOINT_URLS[endpoint]

    return send_inference_request(url, request)

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