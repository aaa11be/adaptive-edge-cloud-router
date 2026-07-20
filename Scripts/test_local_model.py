import time

import torch
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
)


MODEL_NAME = "HuggingFaceTB/SmolLM2-360M-Instruct"


def main() -> None:
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA GPU is not available")

    device = torch.device("cuda")

    print("model:", MODEL_NAME)
    print("device:", torch.cuda.get_device_name(0))
    print("loading tokenizer...")

    tokenizer = AutoTokenizer.from_pretrained(
        MODEL_NAME,
    )

    print("loading model...")

    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,
        torch_dtype=torch.float16,
    )
    model.to(device)
    model.eval()

    messages = [
        {
            "role": "system",
            "content": (
                "You are a concise technical assistant."
            ),
        },
        {
            "role": "user",
            "content": "Explain edge AI in one sentence.",
        },
    ]

    prompt_text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
    )

    inputs = tokenizer(
        prompt_text,
        return_tensors="pt",
    ).to(device)

    torch.cuda.synchronize()
    start_ns = time.perf_counter_ns()

    with torch.inference_mode():
        output_ids = model.generate(
            **inputs,
            max_new_tokens=64,
            do_sample=False,
        )

    torch.cuda.synchronize()
    end_ns = time.perf_counter_ns()

    generated_ids = output_ids[
        0,
        inputs["input_ids"].shape[1]:,
    ]

    output_text = tokenizer.decode(
        generated_ids,
        skip_special_tokens=True,
    )

    inference_ms = (
        end_ns - start_ns
    ) / 1_000_000

    allocated_mb = (
        torch.cuda.memory_allocated()
        / (1024 ** 2)
    )

    reserved_mb = (
        torch.cuda.memory_reserved()
        / (1024 ** 2)
    )

    print()
    print("output:")
    print(output_text.strip())
    print()
    print(f"inference time: {inference_ms:.3f} ms")
    print(f"allocated VRAM: {allocated_mb:.2f} MiB")
    print(f"reserved VRAM: {reserved_mb:.2f} MiB")


if __name__ == "__main__":
    main()