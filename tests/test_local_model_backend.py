import pytest
import torch

from edge_cloud_router.inference import (
    local_model_backend,
)
from edge_cloud_router.schemas import InferenceRequest


class FakeInputs(dict):
    def to(
        self,
        device,
    ):
        return self


class FakeTokenizer:
    def apply_chat_template(
        self,
        messages,
        tokenize: bool,
        add_generation_prompt: bool,
    ) -> str:
        assert messages[-1]["content"] == "Explain edge AI."
        assert tokenize is False
        assert add_generation_prompt is True

        return "formatted prompt"

    def __call__(
        self,
        prompt_text: str,
        return_tensors: str,
    ) -> FakeInputs:
        assert prompt_text == "formatted prompt"
        assert return_tensors == "pt"

        return FakeInputs(
            input_ids=torch.tensor(
                [
                    [10, 20, 30],
                ]
            )
        )

    def decode(
        self,
        token_ids,
        skip_special_tokens: bool,
    ) -> str:
        assert skip_special_tokens is True
        return "  generated answer  "


class FakeModel:
    def to(
        self,
        device,
    ):
        return self

    def eval(self) -> None:
        return None

    def generate(
        self,
        **kwargs,
    ):
        assert kwargs["max_new_tokens"] == 32
        assert kwargs["do_sample"] is False

        return torch.tensor(
            [
                [10, 20, 30, 40, 50],
            ]
        )


def test_local_model_backend_generates_response(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        local_model_backend.torch.cuda,
        "is_available",
        lambda: True,
    )
    monkeypatch.setattr(
        local_model_backend.AutoTokenizer,
        "from_pretrained",
        lambda model_name: FakeTokenizer(),
    )
    monkeypatch.setattr(
        local_model_backend.AutoModelForCausalLM,
        "from_pretrained",
        lambda model_name, dtype: FakeModel(),
    )

    backend = local_model_backend.LocalModelBackend(
        model_name="fake-model",
        max_new_tokens=32,
        quality_score=0.7,
    )

    request = InferenceRequest(
        request_id="local-model-001",
        prompt="Explain edge AI.",
        task_type="smoke",
    )

    response = backend.infer(request)

    assert response.request_id == "local-model-001"
    assert response.endpoint == "local"
    assert response.output_text == "generated answer"
    assert response.quality_score == 0.7
    assert response.configured_processing_delay_ms == 0.0
    assert response.configured_rtt_ms == 0.0


@pytest.mark.parametrize(
    (
        "max_new_tokens",
        "quality_score",
        "expected_message",
    ),
    [
        (
            0,
            0.7,
            "max_new_tokens must be greater than 0",
        ),
        (
            32,
            1.1,
            "quality_score must be between 0 and 1",
        ),
    ],
)

def test_local_model_backend_rejects_invalid_config(
    max_new_tokens: int,
    quality_score: float,
    expected_message: str,
) -> None:
    with pytest.raises(
        ValueError,
        match=expected_message,
    ):
        local_model_backend.LocalModelBackend(
            max_new_tokens=max_new_tokens,
            quality_score=quality_score,
        )