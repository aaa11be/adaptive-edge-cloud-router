# Experiment Plan

## 1. Project objective

Build and evaluate an adaptive router that selects a local or cloud AI endpoint
using request features and system/network state. The final evaluation will
compare adaptive policies against fixed endpoint baselines while preserving a
reproducible paired profile of both endpoints.

## 2. Primary research question

Can a request-aware and system-aware routing policy preserve answer quality while
reducing latency and resource/communication cost relative to Always Local and
Always Cloud policies?

## 3. Current phase objective

Phase 1 does not test the research hypothesis. It validates that the project can:

- represent requests and responses with stable schemas;
- execute identical input against two deterministic backends;
- collect client-side measurements without mixing their semantic meaning;
- append valid, machine-readable JSONL records; and
- reproduce the result through an automated test.

## 4. Phase 1 smoke scenario

One request is executed sequentially against:

- `local`: lower configured delay and lower configured quality;
- `cloud`: higher configured processing delay, additional configured RTT, and
  higher configured quality.

The execution is paired: both records use the same request, experiment, and run
identifiers. Execution order can be changed with a seed to avoid hard-coding an
endpoint-order assumption into later experiments.

## 5. Phase 1 measurements

- Monotonic end-to-end elapsed latency
- Client process CPU percent before/after
- Client process RSS before/after
- System CPU percent before/after
- System memory percent before/after
- Request and response payload bytes
- Configured processing delay and RTT
- Success/error information

Metrics that are not measured are stored as `null`; they are never fabricated.

## 6. Phase 2 primary-task candidate

Use an objectively scored multiple-choice QA subset with exact-match accuracy.
The planned paired profiling procedure is:

1. Freeze a calibration and test split.
2. Run every item on both local and cloud endpoints.
3. Store endpoint latency, correctness, and failure status for each item.
4. Fix utility weights before policy evaluation.
5. Derive Best Static Policy and Per-request Oracle on the test set.
6. Evaluate router regret against the oracle without exposing future endpoint
   outcomes as routing features.

The final public dataset and model pair depend on local hardware, available VRAM,
and access to remote compute.

## 7. Initial hypotheses

- Short/simple requests may favor local execution on latency.
- Requests that require stronger model capability may favor cloud execution on
  objective accuracy.
- Higher RTT should increase the relative utility of local execution.
- A simple rule-based policy may be more robust than a learned policy when the
  profiling dataset is small.

These are hypotheses, not findings.

## 8. Threats to validity to track

- Thermal throttling and background processes
- Endpoint order effects
- Warm-up and model-loading effects
- Inaccurate attribution of system-wide resource counters
- Prompt-format sensitivity
- Small test-set uncertainty
- Utility-weight sensitivity
- Simulation-to-real-network gap

## 9. Immediate completion criteria

Phase 1 is complete when:

- `pytest` passes;
- the smoke command creates exactly two valid JSONL records;
- both endpoint records share one request ID;
- local/cloud configured delays and quality values differ;
- limitations are documented without interpreting mock results as AI findings.
