from typing import Protocol

from edge_cloud_router.schemas import (
    InferenceRequest,
    InferenceResponse,
)


class InferenceBackend(Protocol):

    def infer(
        self,
        request: InferenceRequest,
    ) -> InferenceResponse:
        ...