from __future__ import annotations

from dataclasses import dataclass, field

import torch
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
)

from edge_cloud_router.schemas import (
    InferenceRequest,
    InferenceResponse,
)


DEFAULT_LOCAL_MODEL_NAME = (
    "HuggingFaceTB/SmolLM2-360M-Instruct"
)


@dataclass(slots=True)
class LocalModelBackend:
    """Run a small instruction model on the local CUDA GPU."""

    model_name: str = DEFAULT_LOCAL_MODEL_NAME
    max_new_tokens: int = 64
    quality_score: float = 0.70

    tokenizer: object = field(
        init=False,
        repr=False,
    )
    model: object = field(
        init=False,
        repr=False,
    )
    device: torch.device = field(
        init=False,
        repr=False,
    )

    def __post_init__(self) -> None:
        if self.max_new_tokens <= 0:
            raise ValueError(
                "max_new_tokens must be greater than 0"
            )

        if not 0.0 <= self.quality_score <= 1.0:
            raise ValueError(
                "quality_score must be between 0 and 1"
            )

        if not torch.cuda.is_available():
            raise RuntimeError(
                "CUDA GPU is required for LocalModelBackend"
            )

        self.device = torch.device("cuda")

        self.tokenizer = AutoTokenizer.from_pretrained(
            self.model_name,
        )

        self.model = (
            AutoModelForCausalLM
            .from_pretrained(
                self.model_name,
                dtype=torch.float16,
            )
        )

        self.model.to(self.device)
        self.model.eval()

    def infer(
        self,
        request: InferenceRequest,
    ) -> InferenceResponse:
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a concise technical assistant."
                ),
            },
            {
                "role": "user",
                "content": request.prompt,
            },
        ]

        prompt_text = (
            self.tokenizer
            .apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True,
            )
        )

        inputs = self.tokenizer(
            prompt_text,
            return_tensors="pt",
        ).to(self.device)

        with torch.inference_mode():
            output_ids = self.model.generate(
                **inputs,
                max_new_tokens=self.max_new_tokens,
                do_sample=False,
            )

        generated_ids = output_ids[
            0,
            inputs["input_ids"].shape[1]:,
        ]

        output_text = self.tokenizer.decode(
            generated_ids,
            skip_special_tokens=True,
        ).strip()

        return InferenceResponse(
            request_id=request.request_id,
            endpoint="local",
            output_text=output_text,
            quality_score=self.quality_score,
            configured_processing_delay_ms=0.0,
            configured_rtt_ms=0.0,
        )