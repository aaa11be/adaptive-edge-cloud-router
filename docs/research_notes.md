# Research Notes

## 2026-07-18 — Initial design decisions

### Decisions

* Start with deterministic in-process mock backends rather than FastAPI or real
models.
* Use paired execution from the beginning so the experiment structure supports
later oracle and regret analysis.
* Separate configured RTT from measured RTT; Phase 1 only has configured RTT.
* Record client process metrics separately from system-wide metrics.
* Use `null` for unavailable endpoint/GPU/TTFT measurements.
* Select objectively scored multiple-choice QA as the initial Phase 2 task family,
subject to hardware validation.

### Rationale

The first risk is not model quality but an unreliable experiment pipeline.
Deterministic backends make schema, logging, timing, and reproducibility failures
easier to diagnose before external processes, network transport, and model
runtime variability are introduced.

### Non-findings

No real AI performance result has been produced. Configured mock quality scores
must not be reported as measured accuracy.

## 2026-07-18 — Generated-package validation

### Executed checks

* Installed the local package in editable mode without downloading dependencies.
* Ran the automated test suite: 2 tests passed.
* Ran the Phase 1 smoke benchmark.
* Confirmed that two JSONL records were written and validated.
* Confirmed local/cloud records shared one paired request and had distinct
configured delay/quality conditions.

### Observed scaffold-validation result

* Local elapsed latency: approximately 20.34 ms
* Cloud elapsed latency: approximately 121.03 ms
* Local configured quality: 0.60
* Cloud configured quality: 0.90

These values validate the configured mock pipeline only. They are not real AI
inference findings and should not be cited as project research results.



## 2026-07-18 — Phase 1 Mock Pipeline Validation

### 실험 목적

실제 AI 모델을 연결하기 전에 다음 측정 흐름이 정상적으로 작동하는지 검증했다.

1. 동일한 요청 생성
2. Local 및 Cloud backend에 paired execution
3. 실행시간과 client 자원 정보 측정
4. 공통 스키마로 결과 변환
5. JSONL 파일에 요청별 결과 저장

이번 실험은 실제 Edge–Cloud AI 성능 비교가 아니라 측정·로깅 파이프라인의 smoke test다.

### 실행 명령

```powershell
C:\dev\.venv\Scripts\python.exe -m edge_cloud_router.evaluation.smoke_benchmark --output results/smoke.jsonl --prompt "This is my first edge cloud routing experiment."
```

### 실험 결과

- Local latency: 20.5091 ms
- Local quality score: 0.60
- Local RSS after: 약 30.54 MiB
- Cloud latency: 120.2452 ms
- Cloud quality score: 0.90
- Cloud RSS after: 약 30.39 MiB
- Configured Cloud RTT: 40 ms
- JSONL records: 2
- 두 레코드는 동일한 `run_id`와 `request_id`를 공유했다.

### Mock 설정

- Local processing delay: 약 20 ms
- Cloud processing delay: 약 80 ms
- Cloud configured RTT: 40 ms
- Local quality score: 0.60
- Cloud quality score: 0.90

20 ms, 80 ms, 40 ms는 실제 장비나 논문에서 도출한 수치가 아니다. 다음 조건을 검증하기 위한 테스트 파라미터다.

1. Local과 Cloud의 latency 차이가 운영체제 측정 오차보다 충분히 크게 나타나는가?
2. Cloud 처리시간과 네트워크 지연을 분리해 설정할 수 있는가?
3. 설정한 예상시간과 실제 측정된 경과시간이 비슷하게 기록되는가?
4. 짧은 시간 안에 smoke test를 반복 실행할 수 있는가?

품질 점수 0.60과 0.90 역시 실제 모델 평가 결과가 아니다. Local은 빠르지만 품질이 낮고, Cloud는 느리지만 품질이 높은 가상의 trade-off를 로깅할 수 있는지 검증하기 위해 설정한 상수다.

### 관찰

- 예상 Local latency 약 20 ms에 대해 20.5091 ms가 측정됐다.
- 예상 Cloud latency 약 120 ms에 대해 120.2452 ms가 측정됐다.
- 같은 요청이 동일한 `run_id`와 `request_id`로 두 endpoint에 기록됐다.
- backend 실행 순서는 seed를 이용해 무작위화됐다.
- Local과 Cloud의 RSS 차이는 매우 작았다.

### 해석

현재 Local과 Cloud backend는 별도 프로세스나 실제 모델이 아니라 동일한 Python 프로세스 안에서 실행되는 deterministic mock이다. 따라서 현재 RSS 결과로 endpoint별 모델 메모리를 비교할 수 없다.

`latency_ms`, `timestamp`, payload bytes, JSONL 기록은 실제로 측정·생성된 값이다. 그러나 처리 지연, RTT, 품질 점수는 인위적으로 설정한 값이다.

현재 단계에서 확인한 것은 실제 AI 성능이 아니라 다음 실행 체인의 정상 동작이다.

```text
Request → Backend execution → Measurement → Common schema → JSONL logging
```

### 발견된 한계

- 실제 AI 모델을 실행하지 않았다.
- 실제 HTTP 통신이 없다.
- RTT는 실제 측정값이 아니라 설정된 delay다.
- 품질 점수는 정답 기반 평가 결과가 아니다.
- client CPU 측정값은 짧은 실행 구간 때문에 변동성이 크다.
- Local과 Cloud의 endpoint 자원이 별도로 측정되지 않는다.

### 다음 작업

Local과 Cloud backend를 서로 다른 FastAPI 서버 프로세스로 분리한다. 먼저 동일 PC의 다른 포트에서 HTTP 요청을 수행하여 다음 항목을 구분할 수 있는 구조를 만든다.

- Client end-to-end latency
- Server processing time
- HTTP 및 직렬화 overhead
- Local/Cloud endpoint process