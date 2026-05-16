# ige_prototype_simplified

개인 메모와 LLM을 연결해 아이디어 탐색 흐름을 확인한 초기 PoC입니다.

sample note에서 concept(아이디어 연결 단위)를 추출하고, 주어진 맥락(context)을 기준으로 problem concept와 mechanism concept를 선택한 뒤, 두 축을 조합해 관련 note를 다시 LLM 입력으로 구성합니다.

구현 범위는 Python과 SQLite 기반의 로컬 파이프라인입니다. IGE 전체 설계를 구현한 것이 아닌, 개인 메모와 LLM을 연결해 아이디어 탐색 흐름을 구성하는 초기의 구상을 작은 스케일로 실험한 PoC입니다.


## 1. PoC 소개


PoC 흐름은 다음과 같습니다.

- sample note에서 문제 상황, 제약, 작동 방식처럼 아이디어 연결에 사용할 concept를 추출한다.
- context와 관련된 problem concept와 mechanism concept를 선택한다.
- 두 concept 축을 조합해 관련 note를 다시 불러온다.
- context, concept 조합, 관련 note를 LLM 입력으로 구성한다.
- 서로 다른 관점의 idea output을 생성한다.



## 2. 문제의식과 PoC 구현 방향


1) 문제의식
LLM을 활용하면서, 답변이 주어진 context와 의미적으로 가까운 방향으로 모이고 익숙한 문제해결 프레임 안에서 구성되는 문제가 반복된다고 느꼈습니다. 하지만 개인 자료를 단순히 많이 넣는 방식이나 프롬프트 제어만으로는 자료 간 관계나 다른 해석 경로를 충분히 활용하기 어렵다고 보았습니다.

2) 해결 방향
따라서 IGE 구상은 개인 DB를 단순 context 저장소로 쓰는 것이 아니라,
concept와 note 연결을 활용해 LLM이 다른 탐색 경로를 타도록 만드는 방향에서 출발했습니다.

3) 현재 PoC의 단순화
현재 PoC는 이 구상에서 핵심으로 남은 초기 아이디어 탐색 흐름을 작은 로컬 파이프라인으로 구현한 프로젝트입니다. concept 선택, concept 조합, 관련 note 구성, idea output 생성으로 이어지는 과정이 LLM의 기존 탐색 흐름에 변화를 줄 수 있는지 확인합니다.

4) 제외한 범위
그래프 기반 관계 탐색이나 임베딩 거리 계산은 현재 구현 범위에 넣지 않았습니다.
대신 LLM의 concept 선택과 rank 기반 조합으로 탐색 흐름을 단순화했습니다.


## 3. 전체 파이프라인


전체 파이프라인은 다음 순서로 동작합니다.

1. context 입력
2. SQLite에 저장된 concept 목록 조회
3. context와 관련된 problem concept, mechanism concept 선택
4. problem concept와 mechanism concept 조합
5. 조합별 관련 note 선택
6. 선택된 note를 LLM 입력으로 구성
7. context에 맞는 idea output 생성


## 4. 구현 의도


LLM에 context를 바로 전달해 답변을 생성하는 방식과의 차이는, 가까운 정보를 바로 찾기보다 다른 관점의 note 연결이 생기도록 탐색 경로를 먼저 만든다는 점입니다. 일반적인 사용 방식에서는 LLM이 주어진 context와 의미적으로 가까운 정보나 익숙한 문제해결 프레임을 중심으로 답변을 구성하기 쉽습니다. 이 PoC에서는 바로 답변을 생성하지 않고, 먼저 problem concept와 mechanism concept를 선택한 뒤 두 축을 조합해 관련 note를 다시 구성합니다.

concept 조합 자체가 최종 아이디어를 만드는 것이 아니라, 그 조합을 통해 실제 note를 불러올 때 예상치 못한 연결이 생깁니다. LLM은 context, concept 조합, 관련 note를 함께 보고 idea output을 생성합니다.

부가적인 효과로는 전체 note를 한 번에 전달하지 않고 선택된 관련 note만 사용하므로, LLM 입력 범위가 줄어들고 전체 DB를 그대로 노출하지 않아도 된다는 이점이 있습니다. 즉, 최종 idea output을 생성하는 LLM이 전체 DB에 먼저 접근하는 것이 아니라, 앞 단계에서 선택된 concept 조합과 관련 note만 입력으로 받도록 설계했습니다.


## 5. 실행 방법


API key: GEMINI_API_KEY 환경변수를 사용합니다.

main model: gemini-3.1-flash-lite
fallback model: gemini-2.5-flash-lite

1) 실행 흐름:

```
패키지 설치 -> DB seed(선택) -> 직접 실행 또는 FastAPI 실행 -> sample_output 확인
```

패키지 설치:
```
pip install -r requirements.txt
```

DB seed:
sample note를 읽어 SQLite DB에 note와 concept를 저장합니다.
```
python src/seed_sample_data.py
```

DB seed가 필요한 경우:
- sample_data/notes에 파일을 추가하거나 수정한 경우
- concept_extractor.py의 prompt를 수정한 경우
- DB schema를 수정한 경우

sample_data/notes에 sample note를 추가할 수 있습니다. note 파일을 추가하거나 수정한 뒤에는 DB seed를 다시 실행해야 DB에 반영됩니다.


2) 직접 실행

직접 실행은 로컬에서 idea generation 흐름을 바로 확인하는 방식입니다.

context.txt에 테스트할 문제 상황이나 아이디어 조건을 적은 뒤 실행합니다. 필요하면 context 아래에 sample 상황이나 추가 조건을 붙여 테스트할 수 있습니다.
```
python src/idea_generator.py
```
직접 실행 결과는 터미널에 출력됩니다. 


3) FastAPI 실행

FastAPI 실행은 로컬 API 형태로 같은 파이프라인을 테스트하는 방식입니다.

프로젝트 루트에서 실행:
```
python -m uvicorn app:ige_app --app-dir src --reload
```

API 요청:
```
POST /generate
```
요청할 때는 `context`에 테스트할 문제 상황이나 아이디어 조건을 넣습니다.
```
{ "context": "아이디어 생성 과정에서 LLM이 비슷한 답변으로 수렴하지 않게 하고 싶다." }
```


## 6. 구현된 기능


현재 구현된 범위:

- sample note 파일 로드
- SQLite DB 테이블 생성
- note 저장
- concept 저장
- note와 concept 연결 저장
- context 기반 concept 선택
- problem concept와 mechanism concept 조합
- 관련 note 선택
- LLM 기반 idea output 생성
- FastAPI 기반 /generate 로컬 API

현재 사용 테이블:

| 테이블 | 역할 |
|---|---|
| notes | 원천 note 저장 |
| concepts | 추출된 concept 저장 |
| note_concepts | note와 concept 연결 저장 |


## 7. 파일 구조


주요 파일과 폴더:

| 경로 | 역할 |
|---|---|
| README.md | 프로젝트 설명 |
| requirements.txt | 필요 라이브러리 목록 |
| context.txt | 직접 실행 시 사용할 context 입력 파일 |
| data/ige_prototype.db | SQLite DB 파일 |
| sample_data/notes | 공개 가능한 sample note 파일 |
| sample_output | 주요 실행 결과 예시 |
| docs/run_log.md | 구현 및 병목 기록 일부 정리 |
| docs/output_log.md | Baseline 비교에 사용한 전체 실행 로그 |
| src/memo_db.py | DB 경로와 테이블 생성 |
| src/seed_sample_data.py | sample note를 SQLite DB에 저장 |
| src/concept_extractor.py | note 기반 concept 추출 |
| src/concept_search.py | context 기반 concept 선택 |
| src/collision_engine.py | problem concept와 mechanism concept 조합 |
| src/note_selector.py | 조합별 관련 note 선택 |
| src/idea_generator.py | idea output 생성 |
| src/app.py | FastAPI 기반 API 요청과 응답 처리 |


## 8. 실행 결과 예시


- sample_output/seed_sample_data_sample.txt
- sample_output/concept_search_sample.txt
- sample_output/idea_generator_sample.txt
- sample_output/idea_generator_sample2.txt
- docs/output_log.md

각 파일에서 자세한 실행 결과를 확인할 수 있습니다.


## 9. Baseline 비교


같은 질문을 LLM에 바로 입력하는 방식을 Baseline으로 삼아 IGE output을 비교했습니다.

답변의 논리적 정합성과 실현 가능성은 비교 기준으로 두지 않았습니다. PoC의 목적이 같은 문제 상황에서 다른 탐색 방향이 만들어지는지를 확인하는 것이기 때문입니다. LLM은 context를 바로 입력받아 답변을 생성하고, IGE output은 problem concept, mechanism concept, 관련 note를 거쳐 결과를 생성합니다.

전체 실행 결과는 docs/output_log.md에 기록되어 있습니다.


1) 사용 context

- context 1: 짧은 메모를 모아두는 서비스
- conctex 2: 온라인 학습 서비스

context에 특정 해결 방법을 언급하지는 않았으나, 탐색 로직의 차이를 구분하기 용이하게 하기 위해 LLM이 비교적 익숙한 문제 해결 방향으로 답변하기 쉬운 상황으로 구성했습니다.


2) 비교 기준

비교 기준은 다음 두 가지입니다.

1. context와 무관하게 이탈하지 않는가
2. Baseline과 다른 탐색 방향이 보이는가

첫 번째는 IGE output의 최소 통과 기준이며, 두 번째 기준은 IGE output이 Baseline과 구분되는 탐색 루트를 만들었는지 확인하기 위한 기준입니다.
IGE output이 낯선 방향으로 전개되더라도, context와의 연결을 유지하면 유효한 결과로 보았습니다.


3) 비교 구조

IGE output 3개는 서로 영향을 주는 단계별 결과가 아니라, context 관련성 순으로 선택된 concept 목록에서 서로 다른 순번의 problem concept와 mechanism concept를 조합해 만든 탐색 후보입니다.

3개의 IGE output은 한 번의 pipeline 실행에서 함께 생성되어 독립 시행이 아니므로, 엄밀한 비교에는 한계가 있다고 인지하고 있습니다. 다만 비교의 초점은 IGE output이 익숙한 프레임워크로 수렴하지 않고 같은 context 안에서 여러 탐색 방향으로 분기하는지 확인하는 데 있으므로, 이번 비교 목적에는 충분하다고 판단했습니다.


4) 비교 요약


| Context | Baseline 경향 | IGE output 경향 |
|---|---|---|
| 짧은 메모 서비스 | 자동 회고, 맥락 기반 알림, 기록 재발견 등 | 기억 공고화, private sandbox, 적응형 가이드, 사회적 넛지 등 |
| 온라인 학습 서비스 | 챌린지, 완주 보장, 커뮤니티 기반 학습 운영 등 | 심리적 안전감, 질문과 오류 공유, 비대칭 가격 구조, 사회적 규범 메시지 등 |


5) 확인한 점

두 context 모두에서 Baseline은 문제 상황에 부합하는 익숙한 해결 프레임워크로 수렴했습니다.
짧은 메모 서비스 context에서는 UX 및 제품 설계 관점의 프레임워크로, 온라인 학습 서비스 context에서는 전환율과 재방문 중심의 운영 프레임워크로 수렴했습니다.

반면 IGE output은 단일 프레임워크로 수렴하지 않고, problem concept, mechanism concept, 관련 note의 조합을 통해 여러 방향으로 분기했습니다. 일부는 낯선 방향으로 전개되었지만 context와의 연결은 유지했습니다.
따라서 이번 비교에서 Baseline은 context에 직접 부합하는 도메인 프레임워크로 수렴하는 반면, IGE output은 같은 context 안에서 프레임워크를 고정하지 않고 note의 내용을 기준으로 한 비정형적인 탐색 방향을 생성하는 것을 확인했습니다.


## 10. 구현 한계


현재 PoC는 IGE 구상의 초기 흐름을 작은 범위에서 확인하기 위해, 향후 구조에서는 graph DB나 node, edge 구조로 처리해야 할 관계 탐색 일부를 LLM 판단과 단순 규칙으로 대체했습니다. 구체적으로는 context와 관련된 concept를 LLM이 먼저 선택하고, 이후 collision 조합은 선택된 concept의 rank를 기준으로 구성합니다. 이러한 방식으로 작은 sample data에서 전체 파이프라인을 빠르게 확인할 수 있었지만, concept 간 실제 의미 거리, 관계 방향, 연결 강도를 수치화할 수는 없었습니다.

따라서 이 파이프라인의 한계는 단순히 LLM을 사용한다는 점이 아니라, 관계 기반 구조로 계산되어야 할 탐색 단계 일부를 LLM의 의미 기반 선택과 rank 기반 조합으로 대신하고 있다는 점에 있습니다. 데이터 규모가 작을 때는 흐름 확인이 가능하지만, 데이터가 커질 경우 concept 선택 기준과 관련 note 선택 결과의 재현성, 일관성이 낮아질 수 있습니다. 또한 graph 기반 node, edge 탐색이 없기 때문에 concept 간 관계가 왜 연결되었는지 구조적으로 검증하기 어렵습니다.

구현 과정에서는 데이터 스키마의 중요성도 확인했습니다. 초기 설계에서 concept의 구조를 충분히 분리해두지 않아, 실행 과정에서 데이터를 다시 변환하는 로직이 늘어났습니다. 그 결과 데이터 흐름을 추적하기 어려워졌고, 작은 PoC임에도 중심 데이터의 스키마를 뒤늦게 바꾸는 일이 쉽지 않다는 점을 확인했습니다. 특히 concept처럼 시스템의 중심에 있는 데이터는 추출, 선택, 조합, note 연결 단계에서 반복적으로 참조되므로 초기에 구조를 명확히 잡아두는 것이 필수라는 점을 확인했습니다.

별도로, 현재 PoC에는 idea output의 품질을 자동으로 평가하는 로직이 없습니다. 출력이 실제로 다른 관점을 만들었는지, context와의 관련성을 유지했는지, 반복 실행에서도 안정적인 품질을 보이는지는 아직 직접 확인해야 합니다. 


## 11. 향후 개선 방향


이후 방향은 현재 PoC에서 LLM 판단과 rank 기반 조합으로 단순화한 부분을, IGE 구상에서 의도한 관계 기반 탐색 구조로 옮기는 것입니다.

- graph 기반 관계 탐색 검토
- 중심 데이터인 concept 스키마 정의
- 임베딩 유사도 기반 concept 검색 검토
- output 평가 기준 정량화
- Non-LLM 기반 validator 검토
