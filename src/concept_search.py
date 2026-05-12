import json
import sqlite3
from pathlib import Path
from google import genai

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "ige_prototype.db"
CONTEXT_PATH = BASE_DIR / "context.txt"

MAIN_MODEL_NAME = "gemini-3.1-flash-lite"
BACKUP_MODEL_NAME = "gemini-2.5-flash-lite"


# context(내용) 입력 경로
def get_context():
    return CONTEXT_PATH.read_text(encoding="utf-8")


# --- sqlite DB -> Python list ---

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# sqlite concept table -> concept_table (python)
def fetch_concepts():
    conn = get_connection()

    concept_query = """
    SELECT id, name, type
    FROM concepts
    ORDER BY LENGTH(name), name, type
    """
    concept_rows = conn.execute(concept_query).fetchall()
    conn.close()

    return [dict(row) for row in concept_rows]


def build_llm_concepts_list(concept_table):
    llm_concepts_list = []

    for concept in concept_table:
        llm_concepts_list.append(
             {"name": concept["name"], "type": concept["type"]}
            )
    return llm_concepts_list
        

# --- LLM ---

def gemini_prompt2(context, llm_concepts_list):
    prompt = """
    context를 보고 llm_concepts_list에서 관련된 concept를 선택해줘.

    정의: 
    - context: llm 대화 세션. 사용자 의도, 문제 정의, 제약 조건 정보를 포함.
    - llm_concepts_list: DB에 이미 저장된 concept 목록. 검색과 조합에 쓰는 index item.
    - problem concept: 문제 유형 또는 병목 역할로 사용할 concept
    - mechanism concept: 작동 방식 또는 해결 방식 역할로 사용할 concept
    

    조건:
    - llm_concepts_list에 있는 name만 그대로 사용. 새 concept 생성/name 변경 금지
    - problem 5개, mechanism 5개를 관련성 순서대로 선택
    - 같은 type 안의 의미 중복 제외: 동의어, 상하위 관계, 같은 원인-결과 체인, 추상도 차이 포함
    - json.loads()로 파싱 가능한 JSON만 출력. type은 problem 또는 mechanism만 사용


    출력 형식:
    [
    {"name": "concept name", "type": "problem"},
    {"name": "concept name", "type": "problem"},
    {"name": "concept name", "type": "problem"},
    {"name": "concept name", "type": "problem"},
    {"name": "concept name", "type": "problem"},
    {"name": "concept name", "type": "mechanism"},
    {"name": "concept name", "type": "mechanism"},
    {"name": "concept name", "type": "mechanism"},
    {"name": "concept name", "type": "mechanism"},
    {"name": "concept name", "type": "mechanism"}
    ]

    """

    prompt += f"""

    Context:
    {context}

    llm_concepts_list:
    {json.dumps(llm_concepts_list, ensure_ascii=False)}
    """
    
    return prompt


def call_gemini(prompt):
    client = genai.Client()

    try:
        response = client.models.generate_content(
            model=MAIN_MODEL_NAME,
            contents=prompt
        )
        
        text = response.text.strip().replace("```json", "").replace("```", "")
        return json.loads(text)

    except Exception as e:
        print("---error: MAIN_MODEL 응답오류---")
        print(e)
        print("---BACKUP_MODEL로 다시 시도---")

        try: 
            response = client.models.generate_content(
                model=BACKUP_MODEL_NAME,
                contents=prompt
            )

            text = response.text.strip().replace("```json", "").replace("```", "")
            return json.loads(text)

        except Exception as e:
            print("error: gemini 응답 오류")
            print(e)


# --- restore id (readme에 설명 추가) ---
# selected_concepts = json.loads(text) 리스트

def restore_concept_ids(concept_table, selected_concepts):
    selected_concepts_with_id = []

    for selected in selected_concepts:
        for concept in concept_table:
            if selected["name"] == concept["name"] and selected["type"] == concept["type"]:
                selected_concepts_with_id.append(concept)

    return selected_concepts_with_id


def build_concept_search_result(context, selected_concepts_with_id):
    concept_search_result = {
        "context": context,
        "selected_concepts": selected_concepts_with_id
    }
    return concept_search_result


# --- 통합 함수 ---

""" 
데이터 흐름 기준 정리 
sqlite db concept list(with id) -> concept list obj (with id)-> concept list obj (without id) -> make prompt with concept list obj (without id)
-> llm_api(prompt) + parsing (json txt -> py obj) -> selected_concepts (without id) -> selected_concepts_with_id ->  context + selected_concepts_with_id
"""


def run_concept_search(context):
    concept_table = fetch_concepts()
    llm_concepts_list = build_llm_concepts_list(concept_table)

    prompt = gemini_prompt2(context, llm_concepts_list)
    selected_concepts = call_gemini(prompt)

    selected_concepts_with_id = restore_concept_ids(concept_table, selected_concepts)
    concept_search_result = build_concept_search_result(context, selected_concepts_with_id)

    return concept_search_result


# --- test ---


if __name__ =="__main__":
    context = get_context()
    test = run_concept_search(context)
    print(test)