from edge_cloud_router.api.app_factory import create_app
from edge_cloud_router.inference.local_model_backend import (
    LocalModelBackend,
)


local_model_backend = LocalModelBackend(
    max_new_tokens=64,
    quality_score=0.70,
)

app = create_app(
    title="Adaptive Edge-Cloud Router Local Model API",
    backend=local_model_backend,
)