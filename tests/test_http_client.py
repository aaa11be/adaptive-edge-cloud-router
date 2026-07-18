import httpx
from pytest import MonkeyPatch

from edge_cloud_router.client.http_client import (
    LOCAL_INFER_URL,
    send_inference_request,
)
from edge_cloud_router.schemas import InferenceRequest


class FakeHttpResponse:
    def raise_for_status(self) -> None:
        pass

    def json(self) -> dict[str, object]:
        return {
            "request_id": "client-test-001",
            "endpoint": "local",
            "output_text": "mock-response:test",
            "quality_score": 0.60,
            "configured_processing_delay_ms": 20.0,
            "configured_rtt_ms": 0.0,
            "server_processing_ms": 20.1,
            "success": True,
            "error_type": None,
        }


def test_send_local_inference_request(monkeypatch: MonkeyPatch) -> None:
    def fake_post(
        url: str,
        *,
        json: dict[str, object],
        timeout: float,
    ) -> FakeHttpResponse:
        assert url == LOCAL_INFER_URL
        assert json["request_id"] == "client-test-001"
        assert timeout == 5.0

        return FakeHttpResponse()

    monkeypatch.setattr(httpx, "post", fake_post)

    request = InferenceRequest(
        request_id="client-test-001",
        prompt="What is edge AI?",
        task_type="smoke",
        metadata={},
    )

    response = send_inference_request(LOCAL_INFER_URL, request)

    assert response.endpoint == "local"
    assert response.quality_score == 0.60
    assert response.success is True