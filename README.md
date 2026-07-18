# Adaptive Edge–Cloud AI Router

A research-oriented Python project for evaluating whether request-aware and
system-aware routing can choose between local and cloud AI inference more
usefully than fixed endpoint policies.

This repository currently contains the **Phase 1 deterministic smoke pipeline**.
It validates schemas, client-side resource measurement, JSONL logging, and paired
execution against mock local/cloud backends. It does **not** measure real AI model
performance yet.

## Current scope

- Run the same request through deterministic mock local and cloud backends.
- Configure different processing delays and mock quality scores.
- Measure client process CPU/RSS and system CPU/memory before and after each call.
- Write one JSONL record per endpoint.
- Verify the pipeline with pytest.

## Requirements

- Python 3.11 or later
- CPU-only execution is sufficient

## Installation

### macOS/Linux

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

### Windows PowerShell

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

## Run tests

```bash
pytest
```

## Run the smoke benchmark

```bash
python -m edge_cloud_router.evaluation.smoke_benchmark \
  --output results/smoke.jsonl \
  --prompt "Classify this request for the edge-cloud routing smoke test."
```

Windows PowerShell users can run the same command on one line:

```powershell
python -m edge_cloud_router.evaluation.smoke_benchmark --output results/smoke.jsonl --prompt "Classify this request for the edge-cloud routing smoke test."
```

The installed console command is equivalent:

```bash
edge-cloud-smoke --output results/smoke.jsonl
```

## Success criteria

A successful run should:

1. Exit without an exception.
2. Create `results/smoke.jsonl`.
3. Write exactly two records: one `local` record and one `cloud` record.
4. Use the same `request_id` and `run_id` for both records.
5. Record different configured processing delays and quality scores.
6. Report a higher default elapsed latency for cloud than local, allowing normal
   operating-system scheduling noise.

Inspect the result:

```bash
python - <<'PY'
import json
from pathlib import Path

path = Path("results/smoke.jsonl")
for line in path.read_text(encoding="utf-8").splitlines():
    record = json.loads(line)
    print(record["selected_endpoint"], record["latency_ms"], record["quality_score"])
PY
```

## Research interpretation

The mock backends only validate the measurement and logging pipeline. Their
latency and quality values are deliberately configured; therefore, they cannot
support claims about real local-cloud AI routing. Real model endpoints and an
objectively scored task will be introduced after this smoke pipeline is stable.

## Initial primary-task candidate

The current Phase 2 candidate is a small, fixed subset of **multiple-choice
question answering** with exact-match scoring. This gives a reproducible quality
metric while allowing local and cloud models of different sizes to be compared.
The exact dataset and model pair will be finalized after the user's hardware and
remote-compute options are recorded.

See [`docs/experiment_plan.md`](docs/experiment_plan.md),
[`docs/master_prompt.md`](docs/master_prompt.md), and
[`PROJECT_STATUS.md`](PROJECT_STATUS.md) for the operating rules, plan, and current status.
