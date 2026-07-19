from edge_cloud_router.client.http_client import (
    CLOUD_INFER_URL,
    LOCAL_INFER_URL,
    send_inference_request,
)
from edge_cloud_router.routing.router import (
    RoutingStrategy,
    select_adaptive_endpoint,
    select_endpoint,
)
from edge_cloud_router.schemas import (
    InferenceRequest,
    InferenceResponse,
    RoutingContext,
)


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

def route_adaptive_inference(
    context: RoutingContext,
    request: InferenceRequest,
) -> InferenceResponse:
    endpoint = select_adaptive_endpoint(context)
    url = ENDPOINT_URLS[endpoint]

    return send_inference_request(url, request)

