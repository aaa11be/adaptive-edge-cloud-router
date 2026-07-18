from edge_cloud_router.api.app_factory import create_app
from edge_cloud_router.inference.mock_backend import DeterministicMockBackend


cloud_backend = DeterministicMockBackend(
    endpoint="cloud",
    processing_delay_ms=80.0,
    quality_score=0.90,
    configured_rtt_ms=0.0,
    model_name="deterministic-cloud-http-mock-v1",
)

app = create_app(
    title="Adaptive Edge-Cloud Router Cloud API",
    backend=cloud_backend,
)