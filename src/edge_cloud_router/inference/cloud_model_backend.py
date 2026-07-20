from __future__ import annotations

from dataclasses import dataclass, field
import os
from typing import Any

from huggingface_hub import InferenceClient

from edge_cloud_router.schemas import (
    InferenceRequest,
    InferenceResponse,
)


DEFAULT_CLOUD_MODEL_NAME = (
    "Qwen/Qwen2.5-7B-Instruct"
)


@dataclass(slots=True)
class CloudModelBackend:
    """Call a remote chat model through Hugging Face."""

    model_name: str = DEFAULT_CLOUD_MODEL_NAME
    max_tokens: int = 64
    temperature: float = 0.0
    quality_score: float = 0.90
    token_env_name: str = "HF_TOKEN"

    client: Any = field(
        init=False,
        repr=False,
    )

    def __post_init__(self) -> None:
        if self.max_tokens <= 0:
            raise ValueError(
                "max_tokens must be greater than 0"
            )

        if self.temperature < 0.0:
            raise ValueError(
                "temperature must be non-negative"
            )

        if not 0.0 <= self.quality_score <= 1.0:
            raise ValueError(
                "quality_score must be between 0 and 1"
            )

        token = os.environ.get(
            self.token_env_name,
        )

        if not token:
            raise RuntimeError(
                f"{self.token_env_name} environment "
                "variable is required"
            )

        self.client = InferenceClient(
            token=token,
        )

    def infer(
        self,
        request: InferenceRequest,
    ) -> InferenceResponse:
        response = (
            self.client
            .chat
            .completions
            .create(
                model=self.model_name,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a concise "
                            "technical assistant."
                        ),
                    },
                    {
                        "role": "user",
                        "content": request.prompt,
                    },
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature,
            )
        )

        output_text = (
            response
            .choices[0]
            .message
            .content
        )

        if output_text is None:
            output_text = ""

        return InferenceResponse(
            request_id=request.request_id,
            endpoint="cloud",
            output_text=output_text.strip(),
            quality_score=self.quality_score,
            configured_processing_delay_ms=0.0,
            configured_rtt_ms=0.0,
        )