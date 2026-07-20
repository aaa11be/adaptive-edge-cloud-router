import os
import time

from huggingface_hub import InferenceClient


MODEL_NAME = "Qwen/Qwen2.5-7B-Instruct"


def main() -> None:
    token = os.environ.get("HF_TOKEN")

    if not token:
        raise RuntimeError(
            "HF_TOKEN environment variable is required"
        )

    client = InferenceClient(
        token=token,
    )

    print("model:", MODEL_NAME)
    print("sending cloud inference request...")

    start_ns = time.perf_counter_ns()

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a concise technical assistant."
                ),
            },
            {
                "role": "user",
                "content": (
                    "Explain edge AI in one sentence."
                ),
            },
        ],
        max_tokens=64,
        temperature=0.0,
    )

    end_ns = time.perf_counter_ns()

    output_text = response.choices[0].message.content

    latency_ms = (
        end_ns - start_ns
    ) / 1_000_000

    print()
    print("output:")
    print(output_text)
    print()
    print(f"cloud latency: {latency_ms:.3f} ms")


if __name__ == "__main__":
    main()