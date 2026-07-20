from edge_cloud_router.api.app_factory import create_app
from edge_cloud_router.inference.cloud_model_backend import (
    CloudModelBackend,
)


cloud_model_backend = CloudModelBackend(
    max_tokens=64,
    temperature=0.0,
    quality_score=0.90,
)

app = create_app(
    title="Adaptive Edge-Cloud Router Cloud Model API",
    backend=cloud_model_backend,
)