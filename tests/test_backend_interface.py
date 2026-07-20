from edge_cloud_router.api.app_factory import create_app
from edge_cloud_router.schemas import (
    InferenceRequest,
    InferenceResponse,
)


class FakeInferenceBackend:
    def infer(
        self,
        request: InferenceRequest,
    ) -> InferenceResponse:
        return InferenceResponse(
            request_id=request.request_id,
            endpoint="local",
            output_text="fake model output",
            quality_score=0.7,
            configured_processing_delay_ms=0.0,
            configured_rtt_ms=0.0,
        )


def test_create_app_accepts_generic_backend() -> None:
    backend = FakeInferenceBackend()

    app = create_app(
        title="Test API",
        backend=backend,
    )

    assert app.title == "Test API"