from concept_search import run_concept_search, get_context


def split_concepts(selected_concepts_list):
    selected_mechanism_list = []
    selected_problem_list = []

    for concept in selected_concepts_list:
        if concept["type"] == "mechanism":
            selected_mechanism_list.append(concept)
        if concept["type"] == "problem":
            selected_problem_list.append(concept)

    return selected_mechanism_list, selected_problem_list


# context와 관련도 높은 상위 3개 concept pair 
def build_collision_list(selected_problem_list,selected_mechanism_list):
    collision_list = []

    collision_list.append(
        {
            "problem":selected_problem_list[0],
            "mechanism":selected_mechanism_list[0]
        }
    )

    collision_list.append(
        {
            "problem":selected_problem_list[2],
            "mechanism":selected_mechanism_list[2]
        }
    )

    collision_list.append(
        {
            "problem":selected_problem_list[3],
            "mechanism":selected_mechanism_list[3]
        }
    )

    return collision_list


def build_collision_result(context, collision_list):
    collision_result = {
        "context": context,
        "collisions": collision_list
    }

    return collision_result


# --- 통합 함수 ---
"""
데이터 흐름

run_concept_search의 값. 딕셔너리.  -> 딕셔너리["context"], 딕셔너리["concepts리스트"] 추출 ->

딕셔너리["concepts리스트"] 를 problem list, mechanism list 로 분리 ->

 problem list, mechanism list를 관련도 순으로 collision_list에 3개 추가  -> collision_result = {"context":context, "collisions":collision_list}

"""

def run_collision_engine(context):
    concept_search_result = run_concept_search(context)

    context = concept_search_result["context"]
    selected_concepts_list = concept_search_result["selected_concepts"]

    # 리스트 2개로 분리
    selected_mechanism_list, selected_problem_list = split_concepts(
        selected_concepts_list
    )

    collision_list = build_collision_list(
        selected_problem_list,
        selected_mechanism_list
    )

    collision_result = build_collision_result(context, collision_list)

    return collision_result


# --- test ---


if __name__ == "__main__":
    context = get_context()
    test = run_collision_engine(context)
    print(test)