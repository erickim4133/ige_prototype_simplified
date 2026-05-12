import json
from google import genai
from concept_search import get_context
from note_selector import run_note_selector

MAIN_MODEL_NAME = "gemini-3.1-flash-lite"
BACKUP_MODEL_NAME = "gemini-2.5-flash-lite"


def ige_prompt(note_selector_result):
    context = note_selector_result["context"]
    final_note_inputs = note_selector_result["final_note_inputs"]

    prompt = """
    context와 final_note_inputs를 보고 idea_output을 생성해줘.

    정의: 
    - context: 내용의 맥락 또는 문제의식 구조
    - final_note_inputs: collision pair별로 선택된 problem slot note와 mechanism slot note
    - problem_slot : 문제 관점으로 읽을 note
    - mechanism_slot : 작동 방식 또는 해결 방식 관점으로 읽을 note
    - slot concept: 해당 slot의 note content를 제한하는 필터가 아닌 slot의 concept에 기반한 관점으로 읽을 렌즈
    - note content: 전체를 참고하되, 해당 slot concept를 렌즈로 우선 해석할 note 본문

    조건:
    - 각 item은 독립된 생성 단위. 해당 item의 problem_slot과 mechanism_slot만 근거로 사용한다
    - idea_outputs item 수와 collision_index는 final_note_inputs와 동일하게 유지한다
    - 같은 note_id가 여러 item 또는 같은 item의 다른 slot에 반복되어도, slot concept가 다르면 note에서 주목하는 측면과 해석 방향이 달라야 한다
    - problem_slot과 mechanism_slot의 표면 도메인명을 그대로 반복하지 말고, 그 안의 구조·관계·작동 방식을 추출한다
    - content는 slot concept 렌즈로 분석하여 구조·관계·작동 방식을 추출하는 재료로 사용한다
    - 추출한 구조·관계·작동 방식을 current context의 대상과 사용 상황에 적용한다
    - idea_output은 context 요약, 설명, 평가가 아니라 current context 안에서 실행 가능한 하나의 구체적 접근방법으로 작성한다
    - json.loads() 파싱 가능한 JSON만 출력. 생성 후 형식 검토 필수


출력 형식:
{
  "idea_outputs": [
    {
      "collision_index": 0,
      "idea_output": "..."
    },
    {
      "collision_index": 1,
      "idea_output": "..."
    },
    {
      "collision_index": 2,
      "idea_output": "..."
    }
  ]
}
"""

    prompt += f"""

context:
{context}

final_note_inputs:
{json.dumps(final_note_inputs, ensure_ascii=False)}
"""

    return prompt


# 래퍼런스 출력
def show_collisions(note_selector_result):
    final_note_inputs = note_selector_result["final_note_inputs"]

    collisions = []

    for item in final_note_inputs:
        index = item["collision_index"]
        p_concept = item["problem_slot"]["concept"]["name"]
        m_concept = item["mechanism_slot"]["concept"]["name"]
        p_note_id = item["problem_slot"]["note"]["note_id"]
        m_note_id = item["mechanism_slot"]["note"]["note_id"]

        collisions.append(
            f"index {index} / problem x mechanism: {p_concept}(note_id:{p_note_id}) x {m_concept}(note_id:{m_note_id})"
        )

    return collisions

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


def generate_idea(note_selector_result):
    prompt = ige_prompt(note_selector_result)
    idea_output = call_gemini(prompt)

    return idea_output


def run_idea_generator(context):
    note_selector_result = run_note_selector(context)

    collisions = show_collisions(note_selector_result)
    ige_output = generate_idea(note_selector_result)

    ige_result = {
        "collisions": collisions,
        "ige_outputs": ige_output["idea_outputs"]
    }

    return ige_result

#--- test ---

if __name__ == "__main__":
    context = get_context()
    test = run_idea_generator(context)
    print(test)