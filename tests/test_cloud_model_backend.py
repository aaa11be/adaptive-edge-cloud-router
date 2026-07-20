from types import SimpleNamespace

import pytest

from edge_cloud_router.inference import (
    cloud_model_backend,
)
from edge_cloud_router.schemas import InferenceRequest


class FakeCompletions:
    def __init__(self) -> None:
        self.received_arguments: list[dict] = []

    def create(
        self,
        **kwargs,
    ):
        self.received_arguments.append(kwargs)

        return SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(
                        content="  cloud answer  ",
                    )
                )
            ]
        )


class FakeInferenceClient:
    def __init__(
        self,
        token: str,
    ) -> None:
        self.token = token
        self.completions = FakeCompletions()
        self.chat = SimpleNamespace(
            completions=self.completions,
        )


def test_cloud_model_backend_generates_response(
    monkeypatch,
) -> None:
    created_clients: list[
        FakeInferenceClient
    ] = []

    def fake_client_factory(
        token: str,
    ) -> FakeInferenceClient:
        client = FakeInferenceClient(
            token=token,
        )
        created_clients.append(client)
        return client

    monkeypatch.setenv(
        "HF_TOKEN",
        "test-token",
    )
    monkeypatch.setattr(
        cloud_model_backend,
        "InferenceClient",
        fake_client_factory,
    )

    backend = (
        cloud_model_backend
        .CloudModelBackend(
            model_name="fake-cloud-model",
            max_tokens=32,
            temperature=0.0,
            quality_score=0.9,
        )
    )

    request = InferenceRequest(
        request_id="cloud-model-001",
        prompt="Explain edge AI.",
        task_type="smoke",
    )

    response = backend.infer(request)

    assert len(created_clients) == 1
    assert created_clients[0].token == "test-token"

    assert (
        created_clients[0]
        .completions
        .received_arguments
    ) == [
        {
            "model": "fake-cloud-model",
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a concise "
                        "technical assistant."
                    ),
                },
                {
                    "role": "user",
                    "content": "Explain edge AI.",
                },
            ],
            "max_tokens": 32,
            "temperature": 0.0,
        }
    ]

    assert response.request_id == "cloud-model-001"
    assert response.endpoint == "cloud"
    assert response.output_text == "cloud answer"
    assert response.quality_score == 0.9
    assert response.configured_processing_delay_ms == 0.0
    assert response.configured_rtt_ms == 0.0


def test_cloud_model_backend_requires_token(
    monkeypatch,
) -> None:
    monkeypatch.delenv(
        "HF_TOKEN",
        raising=False,
    )

    with pytest.raises(
        RuntimeError,
        match=(
            "HF_TOKEN environment variable "
            "is required"
        ),
    ):
        cloud_model_backend.CloudModelBackend()


@pytest.mark.parametrize(
    (
        "max_tokens",
        "temperature",
        "quality_score",
        "expected_message",
    ),
    [
        (
            0,
            0.0,
            0.9,
            "max_tokens must be greater than 0",
        ),
        (
            32,
            -0.1,
            0.9,
            "temperature must be non-negative",
        ),
        (
            32,
            0.0,
            1.1,
            "quality_score must be between 0 and 1",
        ),
    ],
)
def test_cloud_model_backend_rejects_invalid_config(
    monkeypatch,
    max_tokens: int,
    temperature: float,
    quality_score: float,
    expected_message: str,
) -> None:
    monkeypatch.setenv(
        "HF_TOKEN",
        "test-token",
    )

    with pytest.raises(
        ValueError,
        match=expected_message,
    ):
        cloud_model_backend.CloudModelBackend(
            max_tokens=max_tokens,
            temperature=temperature,
            quality_score=quality_score,
        )

def test_cloud_model_backend_probe_calls_remote_model(
    monkeypatch,
) -> None:
    created_clients: list[
        FakeInferenceClient
    ] = []

    def fake_client_factory(
        token: str,
    ) -> FakeInferenceClient:
        client = FakeInferenceClient(
            token=token,
        )
        created_clients.append(client)
        return client

    monkeypatch.setenv(
        "HF_TOKEN",
        "test-token",
    )
    monkeypatch.setattr(
        cloud_model_backend,
        "InferenceClient",
        fake_client_factory,
    )

    backend = (
        cloud_model_backend
        .CloudModelBackend(
            model_name="fake-cloud-model",
        )
    )

    output_text = backend.probe()

    assert output_text == "cloud answer"

    assert (
        created_clients[0]
        .completions
        .received_arguments
    ) == [
        {
            "model": "fake-cloud-model",
            "messages": [
                {
                    "role": "user",
                    "content": "Reply with OK.",
                },
            ],
            "max_tokens": 1,
            "temperature": 0.0,
        }
    ]