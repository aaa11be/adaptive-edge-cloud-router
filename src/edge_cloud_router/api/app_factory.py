import time

from fastapi import FastAPI

from edge_cloud_router.inference.backend import (
    InferenceBackend,
)
from edge_cloud_router.schemas import (
    InferenceRequest,
    InferenceResponse,
)


def create_app(
    title: str,
    backend: InferenceBackend,
) -> FastAPI:
    app = FastAPI(title=title)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post(
        "/infer",
        response_model=InferenceResponse,
    )
    def infer_endpoint(
        request: InferenceRequest,
    ) -> InferenceResponse:
        start_ns = time.perf_counter_ns()

        response = backend.infer(request)

        end_ns = time.perf_counter_ns()

        response.server_processing_ms = (
            end_ns - start_ns
        ) / 1_000_000

        return response

    return app