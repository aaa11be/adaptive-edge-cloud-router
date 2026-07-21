## 본 실험의 목적
    - 본 실험의 목적은 Local AI 모델과 Cloud AI 모델을 하나의 시스템 안에서 연결하고, 개인정보보호 여부, 요구 Quality, Cloud 사용 가능 여부, 최근 Latency를 기준으로 추론 위치를 동적으로 선택하는 Adaptive Edge–Cloud AI Router의 동작을 확인하는 것임.  
    - 단순히 Local 모델과 Cloud 모델의 성능을 비교하는 것이 아니라, 실제 추론 결과를 바탕으로 각 endpoint의 Latency를 지속적으로 갱신하고, 상황에 따라 더 적절한 환경을 선택할 수 있는지 검증하는 데 목적이 있음.  
    - 또한 Local이 Cloud보다 빠를 것이라는 초기 가정이 실제 환경에서도 성립하는지 확인하고, 예상과 다른 결과가 발생했을 때 모델 성능, 네트워크, 하드웨어 환경이 라우팅 결과에 어떤 영향을 주는지 살펴보고자 함.  
    - 최종적으로는 Edge와 Cloud의 장단점을 하나의 기준으로 단순 비교하기보다, 요청 조건과 실행환경 상태에 따라 선택하는 정책 기반 추론 시스템의 가능성을 확인하는 것을 목표로 함.

## 실험 환경 정의
    1. Local 모델
        - HuggingFaceTB/SmolLM2-360M-Instruct
    2. Cloud 모델
        - Qwen/Qwen2.5-7B-Instruct
    3. GPU 및 실행환경
        - GPU: NVIDIA GeForce RTX 3060 Ti
        - VRAM: 8GB
        - 운영체제: Windows
        - Python: 3.14.3
        - Local API: 127.0.0.1:8000
        - Cloud Proxy API: 127.0.0.1:8001
        - 주요 프레임워크: FastAPI, PyTorch, Transformers, HTTPX
    4. 요청 프롬프트
        - "Explain edge AI in one short sentence.", 모든 실험에 동일 프롬프트 사용
    5. 웜업 횟수
        - 각 1회
    6. 측정 요건 수
        - 요구 Quality, Cloud사용 가능 여부, 개인정보보호 여부, Local/Cloud Latency, 각 endpoint의 최소 관측 횟수, Cloud probe 결과

## 라우팅 조건
    1. 초기 지연 추정값
        - Local의 경우 3870ms, Cloud의 경우 1144ms를 초기 추정값으로 설정함.  
        - 해당 값은 실제 모델을 대상으로 앞서 수행한 5회 벤치마크 평균을 기준으로 설정함.  
        - 초기 Mock 환경에서는 Local 20ms, Cloud 80ms로 가정하였음. 당시에는 Cloud가 네트워크 지연으로 인해 Local보다 느릴 것이라고 판단했기 때문
        - 하지만 실제 모델을 연결한 결과 Cloud가 Local보다 빠르게 나타났기 때문에 실제 Runtime에서는 20ms, 80ms 값을 사용하지 않음
    2. EWMA α
        - EWMA의 α값은 0.3으로 설정. 0.5의 경우 예상치 못한 장애로 인한 latency들에 대해 가중치가 너무 높게 들어가고, 평균값이 쉽게 흔들릴 수 있는 우려를 방지.
        - 반대로 α값이 너무 작으면 최신 서버 상태를 늦게 반영할 수 있기 때문에, 안정성과 최신성 사이의 절충값으로 0.3을 선택
    3. 최소 관측 횟수
        - Local과 Cloud 각각 최소 1회로 설정함.  
        - 초기 상태에서는 두 endpoint의 실제 Runtime 결과가 없기 때문에 Local을 먼저 1회 탐색하고, 이후 Cloud를 1회 탐색함. 
        - 두 endpoint 모두 최소 관측 횟수를 충족한 이후부터 EWMA 예상 latency를 기준으로 Adaptive Routing을 수행함. 
        - 단, 이후 추론에 있어서 개인정보보호, Cloud 사용 가능 여부, 품질 조건이 더 우선시됨
    4. 품질 기준
        - Local의 경우 0.7, Cloud의 경우 0.9. 
        - Local 모델은 품질은 낮지만 개인정보보호, 원격 네트워크지연 최소화를 통해 빠르고 안전한 output을 받을 수 있다라고 예상
        - Cloud 모델의 경우 클라우드 서버의 자원을 활용하기 때문에 모델 선택의 자유도가 매우 높아 품질 점수를 높게 설정
    5. Probe TTL
        - Local과 Cloud의 라우팅 정책 중 Probe TTL을 넣어, 보조지표로 활용. 이를 통해 네트워크를 포함한 Cloud 전반의 혼잡 상태를 간접적으로 파악함. 캐시가 살아있는 동안은 Cloud 서버에 동일한 Probe 요청을 보내지 않음

## 실험 결과
    1. 요청별 endpoint 선택
        - 제일 처음 분기는 "개인정보보호 정책"임. 아무리 Quality가 중요해도 개인정보보호가 필요하다면 무조건 Local을 선택. 그 이후는 Quality, Latency, Cloud 사용 가능 여부에 맞게 Cloud or Local 모델 선택.
    2. Local/Cloud 처리시간
        - 처음에는 Local이 Cloud에 비해 Latency가 확실히 적을것이라 예상했지만, 실험 결과 Cloud의 Latency가 Local에 비해 확연히 적음 (Local의 평균 latency: 약 3000ms, Cloud의 평균 Latency: 약 1000ms)
        - 이유는 Cloud 서버 자체의 네트워크/추론 환경 최적화, Input 데이터가 작은 추론요청이기 때문에 모델 성능이 더 좋은 Cloud의 요청 처리 시간이 훨 적음 등의 이유로 인하여 Cloud의 Latency가 local에 비해 확연히 적음.
    3. EWMA 변화
        - Local의 경우 초기 관측 이후 다시 선택되지 않았기 때문에 EWMA의 변화가 거의 없었음. Local의 초기 추정값은 3870ms였으며, 첫 관측 이후 약 3409ms로 낮아짐
        - Cloud의 경우 EWMA가 첫 연결 후 평균적으로 낮아지지만, Cloud 서버/네트워크 지연으로 인해 중간중간 EWMA의 값이 확 오르는 경향이 있음.
    4. 관측 횟수
        - Local 1회, Cloud 4회
    5. probe 캐시 동작
        - Runtime의 기본 Probe 캐시 TTL은 10초이며, 이번 실험에서는 실험 도중 캐시가 만료되지 않도록 60초로 설정함.  
        - 캐시가 살아있는 동안에는 Cloud 서버에 동일한 Probe 요청을 다시 보내지 않고 기존 결과를 재사용함

## 해석
    1. 초기 탐색이 정상 수행됐는가
        - Local, Cloud 둘 다 정상 수행이 되었지만, 예상과 다르게 Cloud가 Local에 비해 End-to-End 처리량(Client가 Server에 요청 후 응답을 받는 시간)이 훨씬 빨랐음
        - 이유는 실험결과로도 나왔듯, Cloud의 네트워크/추론 환경 최적화로 인한 Latency 최소화.
    2. 왜 이후 Cloud가 선택됐는지
        - 개인정보보호가 필요하지 않는 한, Cloud가 정상 사용가능한 환경에서 Latency와 Quality 둘 다 Local에 비해 우수하기 때문에 Local모델을 선택할 이유가 없음.
    3. 지연 변동에 의한 EWMA의 반응
        - α 값이 0.3이기 때문에 Cloud에서 네트워크 지연, 혹은 장애가 발생시 EWMA의 값이 눈에 띄게 변동되는 것이 확인됨.
        - EWMA의 값이 어느정도 평균을 유지해야 되지만, 최신의 Cloud 서버 상태도 반영해야 하기 때문에 EWMA의 값으로 현재 Cloud 서버의 추세를 간헐적으로 파악이 가능

## 한계
    1. Client 수, 요청 수가 적음
        - 단일 환경에서만 실험하다 보니 멀티 테넌트, 다중요청 상황에서의 부하 상황을 고려하지 못함. 그러다보니 실 서비스 환경과는 다소 동떨어진 실험이 되어버림
    2. Quality 점수가 실제 평가값이 아닌 설정값
        - Quality 점수를 Local과 Cloud 둘 다 고정값으로 사용함. Local은 0.7, Cloud는 0.9
        - 이유는, 하드웨어의 성능으로 인해 Local에서 상위모델을 돌리지 못하였고, 그렇기때문에 동 모델로 비교할 수가 없어 Local보다는 Cloud에 더 좋은 모델을 설정하였음. 
        - 또한 본 실험의 목적이 각 모델간의 성능을 비교하는것이 주 목적은 아니였기 때문에 Cloud의 모델의 Quality 점수를 더 높게 할당.
    3. 서로 다른 모델을 사용한 시스템 수준 비교
        - Local과 Cloud에서 서로 다른 모델과 서로 다른 하드웨어 환경을 사용함. 이로 인해 모델 자체의 성능만을 비교하거나, 각 환경의 시스템 성능만을 따로 비교하기 어려움.  
        - 결국 모델, 하드웨어, 네트워크 환경이 모두 포함된 시스템 수준의 비교가 되었으며, 이로 인해 초기 예측과 실제 결과가 많이 달라졌음.