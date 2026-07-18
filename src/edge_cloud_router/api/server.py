from edge_cloud_router.api.app_factory import create_app
from edge_cloud_router.inference.mock_backend import DeterministicMockBackend

local_backend = DeterministicMockBackend(
    endpoint="local",
    processing_delay_ms=20.0,
    quality_score=0.60,
    configured_rtt_ms=0.0,
    model_name="deterministic-local-http-mock-v1",
)

app = create_app(
    title="Adaptive Edge-Cloud Router API",
    backend=local_backend,
)