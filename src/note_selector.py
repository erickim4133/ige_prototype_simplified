import json
from google import genai

from collision_engine import run_collision_engine
from concept_search import get_context
from memo_db import get_connection

MAIN_MODEL_NAME = "gemini-3.1-flash-lite"
BACKUP_MODEL_NAME = "gemini-2.5-flash-lite"


def get_note_ids_by_concept_id(concept_id):
    connection = get_connection()
    cursor = connection.cursor()
    
    cursor.execute(
        """
        SELECT DISTINCT note_id
        FROM note_concepts
        WHERE concept_id = ?
        ORDER BY note_id
        """,
        (concept_id,)
    )

    rows = cursor.fetchall()
    connection.close()

    note_ids = []

    for row in rows:
        note_ids.append(row[0])

    return note_ids


def get_linked_concepts_by_note_id(note_id):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT concepts.id, concepts.name, concepts.type
        FROM note_concepts
        JOIN concepts
        ON note_concepts.concept_id = concepts.id
        WHERE note_concepts.note_id = ?
        ORDER BY concepts.id
        """,
        (note_id,)
    )

    rows = cursor.fetchall()
    connection.close()

    linked_concepts = []

    for row in rows:
        linked_concepts.append(
            {
                "concept_id": row[0],
                "concept_name": row[1],
                "concept_type": row[2]
            }
        )

    return linked_concepts


def build_slot_candidates(concept_id):
    note_ids = get_note_ids_by_concept_id(concept_id)

    candidates = []

    for note_id in note_ids:
        linked_concepts = get_linked_concepts_by_note_id(note_id)

        candidates.append(
            {
                "note_id": note_id,
                "linked_concepts": linked_concepts
            }
        )
    return candidates


def build_selector_input(collision_result):
    collisions = collision_result["collisions"]

    selector_collisions = []

    collision_index = 0

    for collision in collisions:
        problem_concept_id = collision["problem"]["id"]
        mechanism_concept_id = collision["mechanism"]["id"]

        problem_slot_candidates = build_slot_candidates(problem_concept_id)
        mechanism_slot_candidates = build_slot_candidates(mechanism_concept_id)

        selector_collisions.append(
            {
                "collision_index": collision_index,
                "problem_slot_candidates": problem_slot_candidates,
                "mechanism_slot_candidates": mechanism_slot_candidates
            }
        )
        collision_index = collision_index + 1

    selector_input = {
        "collisions": selector_collisions
    }

    return selector_input


# --- LLM ---


def build_selector_prompt(selector_input):
    prompt = """
    selector_input을 보고 각 collision마다 사용할 note_id를 선택해줘.

    정의:
    -selector_input: collision별 problem slot 후보 note와 mechanism slot 후보 목록
    -problem_slot_candidates: problem concept와 연결된 note 후보
    -mechanism_slot_candidates: mechanism concept와 연결된 note 후보
    -linked_concepts: 해당 note에 연결된 concept 목록 
    -note_id: 실제 note 로드용 id

    조건:
    -selector_input에 있는 note_id만 선택 
    -각 collision마다 problem_note_id 1개, mechanism_note_id 1개 선택
    -problem_note_id는 해당 collision의 problem_slot_candidates 안에서만 선택
    -mechanism_note_id는 해당 collision의 mechanism_slot_candidates 안에서만 선택
    -같은 collision 내 problem/mechanism note_id 중복 허용, 단 다른 후보 있으면 서로 다른 note_id 우선
    -새로운 note_id 생성 금지
    -json.loads()로 바로 파싱 가능한 JSON만 출력

    출력 형식:
    [
    {
    "collision_index": 0,
    "problem_note_id": 1,
    "mechanism_note_id": 2
    }
    ]
    """

    prompt += f"""
    selector_input:
    {json.dumps(selector_input, ensure_ascii=False)}
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


#

def select_note_with_llm(selector_input):
    prompt = build_selector_prompt(selector_input)
    selector_output = call_gemini(prompt)

    return selector_output


# --- sqlite 조회 함수 ---


def load_note_by_id(note_id):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT id, content
        FROM notes
        WHERE id =?
        """
    ,(note_id,)
    )

    row = cursor.fetchone()
    connection.close()

    note = {
        "note_id": row[0],
        "content": row[1]
    }

    return note


def build_final_note_inputs(collision_result,note_selector_output):
    collisions = collision_result["collisions"]

    final_note_inputs = []

    for selected in note_selector_output:
        collision_index = selected["collision_index"]

        collision = collisions[collision_index]

        problem_concept = collision["problem"]
        mechanism_concept = collision["mechanism"]

        problem_note = load_note_by_id(selected["problem_note_id"])
        mechanism_note = load_note_by_id(selected["mechanism_note_id"])

        final_note_inputs.append(
            {
                "collision_index": collision_index,
                "problem_slot": {
                    "concept": problem_concept,
                    "note": problem_note
                },
                "mechanism_slot": {
                    "concept":mechanism_concept,
                    "note":mechanism_note
                }
            }
        )

    return final_note_inputs


# --- 통합함수 ---
# collisions = {"context":context, "collisions":collision_list}의 collision_list

def run_note_selector(context):
    collision_result = run_collision_engine(context)

    selector_input = build_selector_input(collision_result)
    selector_output = select_note_with_llm(selector_input)

    final_note_inputs = build_final_note_inputs(
        collision_result,
        selector_output
    )

    note_selector_result = {
        "context": collision_result["context"],
        "collisions": collision_result["collisions"],
        "final_note_inputs": final_note_inputs
    }

    return note_selector_result
# --- test ---

if __name__ == "__main__":

    context = get_context()
    test = run_note_selector(context)
    print(test)