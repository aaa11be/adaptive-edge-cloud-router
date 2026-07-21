# 실험 계획
## 1. 프로젝트 목표
  요청 특성과 시스템·네트워크 상태를 활용하여 Local 또는 Cloud AI endpoint를 선택하는 Adaptive Router를 구현하고 평가한다.
  최종 평가에서는 두 endpoint의 재현 가능한 paired profile을 유지한 상태에서 Adaptive Routing 정책을 Always Local, Always Cloud 고정 정책과 비교한다.

## 2. 주요 연구 질문
  요청과 시스템 상태를 고려하는 라우팅 정책이 Always Local, Always Cloud 정책과 비교했을 때 응답 품질을 유지하면서 latency와 자원·통신 비용을 줄일 수 있는가?

## 3. 현재 단계의 목표
  Phase 1은 연구 가설을 검증하는 단계가 아니다. 현재 단계에서는 프로젝트가 다음 기능을 정상적으로 수행할 수 있는지 확인한다.
    - 안정적인 schema를 사용하여 요청과 응답을 표현
    - 동일한 입력을 두 개의 deterministic backend에서 실행
    - 각 측정값의 의미가 섞이지 않도록 client 측 지표 수집
    - 유효하고 기계가 읽을 수 있는 JSONL record 추가
    - 자동화된 테스트를 통해 동일한 결과 재현

## 4. Phase 1 Smoke 시나리오
  하나의 요청을 다음 두 endpoint에서 순차적으로 실행한다.
    - local: 설정된 처리 지연과 품질이 상대적으로 낮음
    - cloud: 설정된 처리 지연이 더 길고 추가 RTT가 존재하지만 품질은 더 높음
  두 실행 결과는 paired 방식으로 기록한다. 두 record는 동일한 request ID, experiment ID, run ID를 사용한다.
  실행 순서는 seed를 통해 변경할 수 있도록 하여, 이후 실험에서 특정 endpoint가 항상 먼저 실행된다는 가정이 고정되지 않도록 한다.

## 5. Phase 1 측정 항목
  - Monotonic clock을 기준으로 측정한 end-to-end latency
  - Client process의 실행 전·후 CPU 사용률
  - Client process의 실행 전·후 RSS 메모리
  - 시스템 전체의 실행 전·후 CPU 사용률
  - 시스템 전체의 실행 전·후 메모리 사용률
  - 요청 및 응답 payload 크기
  - 설정된 processing delay 및 RTT
  - 성공 여부와 오류 정보
  - 실제로 측정하지 않은 metric은 임의의 값으로 생성하지 않고 null로 저장한다.

## 6. Phase 2 주요 Task 후보
  Exact-match accuracy로 객관적인 평가가 가능한 객관식 QA 데이터셋의 일부를 사용한다.
  계획된 paired profiling 절차는 다음과 같다.
  - Calibration split과 test split을 고정한다.
  - 모든 문항을 Local과 Cloud endpoint에서 각각 실행한다.
  - 각 문항에 대한 endpoint latency, 정답 여부, 실패 상태를 저장한다.
  - 정책 평가 전에 utility weight를 고정한다.
  - Test set에서 Best Static Policy와 Per-request Oracle을 계산한다.
  - 미래 endpoint의 실행 결과를 routing feature로 노출하지 않은 상태에서 Oracle 대비 Router의 regret을 평가한다.
  최종적으로 공개할 데이터셋과 모델 조합은 Local 하드웨어, 사용 가능한 VRAM, 원격 연산 자원 접근 가능 여부에 따라 결정한다.

## 7. 초기 가설
  - 짧고 단순한 요청은 latency 측면에서 Local 실행이 유리할 수 있다.
  - 더 높은 모델 성능이 필요한 요청은 객관적인 정확도 측면에서 Cloud 실행이 유리할 수 있다.
  - RTT가 높아질수록 Local 실행의 상대적인 utility가 높아질 수 있다.
  - Profiling 데이터셋이 작은 경우 학습 기반 정책보다 단순한 rule-based 정책이 더 안정적일 수 있다.
위 내용은 실험 결과가 아니라 가설이다.

## 8. 추적해야 할 타당성 위협
  - Thermal throttling 및 background process
  - Endpoint 실행 순서에 따른 영향
  - Warm-up 및 model loading 영향
  - 시스템 전체 resource counter의 부정확한 원인 귀속
  - Prompt format에 따른 민감도
  - 작은 test set으로 인한 불확실성
  - Utility weight 설정에 따른 민감도
  - Simulation 환경과 실제 network 환경의 차이

## 9. 즉시 완료 기준
  - 다음 조건을 모두 만족하면 Phase 1이 완료된 것으로 판단한다.
  - pytest가 통과함
  - Smoke command 실행 시 정확히 2개의 유효한 JSONL record가 생성됨
  - 두 endpoint record가 동일한 request ID를 공유함
  - Local과 Cloud에 설정된 delay와 quality 값이 서로 다름
  - Mock 결과를 실제 AI 성능 결과로 해석하지 않고 한계가 문서화됨