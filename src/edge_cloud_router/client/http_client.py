import httpx

from edge_cloud_router.schemas import InferenceRequest, InferenceResponse


LOCAL_INFER_URL = "http://127.0.0.1:8000/infer"
CLOUD_INFER_URL = "http://127.0.0.1:8001/infer"

DEFAULT_TIMEOUT_S = 5.0

HTTP_CLIENT = httpx.Client(timeout=DEFAULT_TIMEOUT_S)


def send_inference_request(
    url: str,
    request: InferenceRequest,
) -> InferenceResponse:
    response = HTTP_CLIENT.post(
        url,
        json=request.model_dump(mode="json"),
    )

    response.raise_for_status()

    return InferenceResponse.model_validate(response.json())