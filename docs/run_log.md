
# run log  

---

schema 변경

- 초기 schema: key_items / note_key_items / key_type 구조 → 전면 폐기
- concept 중심으로 용어 재정의. DB 파일 삭제 후 재생성
- 최종 schema 근거: concepts(id, name, type) + note_concepts(note_id, concept_id)
- concept_items → concepts 단순화 시점에 keywords 컬럼 제거
- extract_concepts() 출력도 wrapper 없는 top-level list로 맞춤

- 초기 schema가 구현 흐름과 어긋나면 이후 단계에서 데이터 변환 로직이 불어남. 즉  DB schema와 LLM 출력 구조를 맞추면 추출 → 선택 → 조합 → note 연결 전 단계의 복잡도가 줄어듦.

---

입력 방식 변경

- question 기반 direct match → conversation context 기반 concept selector로 변경
- concept_search.py 역할: 질문 검색기 → context 기반 selector로 재정의
- LLM에 전달하는 필드: concept name / type만
- 전달하지 않는 필드: id, note_id, title, content, summary

- 전체 DB를 직접 노출하지 않아도 된다는 게 PoC 핵심 의도 중 하나.  concept 선택을 LLM 판단으로 대체하는 구조 → 재현성과 일관성 약화. 

한계 목록:

- name/type만으로는 LLM이 관계를 과추론할 수 있음
- name/type으로 id를 복원할 때 애매한 케이스 발생
- concept 간 의미 거리, 관계 방향, 연결 강도 수치화 없음
- concept 선택은 실행 가능성 확인 용도로는 기능하지만 llm 기반이라 검증 불가

---

concepts 조회 순서 변경

- ORDER BY LENGTH(name), name, type
- LLM에는 DB id 제거한 name/type list만 전달
- 목적: 저장 순서가 note 묶음을 암시하는 정도를 줄이기 위한 보조 장치
- 편향 완전히 제거하려면 별도 index 설계, embedding 기반 검색, graph 관계 구조 필요.

---

collision_engine.py rank 기반 조합

- run_concept_search() 결과에서 context와 selected_concepts 추출
- selected concept를 mechanism list와 problem list로 분리
- 관련도 순서 기반으로 collision pair 3개 생성

전제: llm이 concept를 관련도 순서로 리스트로 반환

초안(가장 가까운 rank 조합 우선):

- collision 0 = problem[0] × mechanism[0]
- collision 1 = problem[0] × mechanism[1]
- collision 2 = problem[1] × mechanism[0]

- 안정적이지만 problem[0]과 mechanism[0]이 반복되어 세 collision이 같은 방향으로 수렴할 수 있음.

변경:  concept 추출을 각 5개로 늘리고, rank 간격 조정

- 00 / 22 / 33 → 작은 pool에서 안정성과 다양성의 균형 배치
- 00 / 22 / 44 → 같은 pool에서 더 먼 rank 조합 포함하는 실험 배치

- 두 방식 모두 실제 의미 기반 거리 계산이 아니라 llm이 우선순위 뽑는 rank 방식임.   
- 현재 배치는 problem 5개, mechanism 5개 기준. 
- pool이 커지면 같은 간격이 상대적으로 좁아지고, 작아지면 너무 멀게 작동함.


---

같은 collision pair 내 note_id 중복 문제

note_id:2가 여러 collision에 반복되는 병목 확인

원인:
- sample note 수가 적음
- note 하나가 여러 problem/mechanism concept를 동시에 보유하기 때문

개선:
- pair 내부 note_id 중복 금지 규칙 제거
- 후보가 여러 개면 다른 note 우선하되 같은 note_id도 허용
- 코드로 억지 보정하지 않는 쪽으로 결정

- 구조적 개선은 sample note 추가, rank 보완, graph 기반 관계 탐색. 
- 같은 note_id가 problem/mechanism slot에 들어와도 서로 다른 concept lens로 읽히는 구조로 해석. 중복 제거가 아니라 slot 관점 차이로 처리한 것.  


---

현재 상태 요약 및 개선 우선순위

현재 상태:

- 짧거나 애매한 입력 → DB 안의 가까운 concept로 수렴하는 경향
- sample note pool이 작아 note_id 반복과 출력 유사성 발생
- 출력 다양성, context 관련성, 반복 실행 안정성은 반복 검증 안 함