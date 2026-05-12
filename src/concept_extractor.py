import os
import json
from google import genai


API_KEY = os.environ.get("GEMINI_API_KEY")
MAIN_MODEL = "gemini-3.1-flash-lite"
BACKUP_MODEL = "gemini-2.5-flash-lite"

def gemini_prompt(title, content):
    prompt = """
    다음 note에서 concept를 추출해줘.

    정의:
    - concept: Value(note 내용)에서 추출된 의미 단위. 검색과 조합에 쓰는 index item.
    - problem concept: note 안에서 문제로 읽히는 구조
    - mechanism concept: note 안에서 작동, 해결, 변화로 읽히는 구조

    조건:
    - mechanism concept 1~3개
    - problem concept 1~3개
    - JSON만 출력
    - type은 mechanism 또는 problem만 사용

    concept name 작성 기준:
    - 너무 긴 문장이 아닌 짧은 concept 이름으로 출력한다
    - 서로 다른 문제 구조와 작동 구조가 드러나는 항목을 우선 추출한다
    - 도메인 고유명사를 concept name의 중심어로 쓰지 않는다. 중심 의미는 기능, 구조, 관계로 표현한다.
    - note의 구조를 담는다
    - 서로 다른 note에서 추출된 concept와 구분될 만큼 구체적이어야 한다
    - 추상적인 단어 하나만 사용하지 않는다. ex: 문제, 방법, 분석, 시스템


    출력 형식:
   [
   {"name": "concept name", "type": "problem"},
   {"name": "concept name", "type": "mechanism"}
   ]

    ---

    예시("concept" 2개일 떄):
    
   [
   {"name": "유사 후보 반복에 따른 결과 수렴", "type": "problem"},
   {"name": "구조 차이 기반 후보 분산", "type": "mechanism"}
   ]
        
   """      
    prompt += f"""

    Note Title: 
    {title}

    Note Content: 
    {content}
    """
    
    return prompt

def extract_concepts(title, content):
    if API_KEY is None:
        print("error: GEMINI_API_KEY 환경변수 필요")
        return

    client = genai.Client(api_key= API_KEY)
    prompt = gemini_prompt(title, content)

    try:
        response = client.models.generate_content(
            model = MAIN_MODEL,
            contents = prompt
        )

    except Exception as e:
        print("---error: MAIN_MODEL 응답오류---")
        print(e)
        print("---BACKUP_MODEL로 다시 시도---")

        try:
            response = client.models.generate_content(
                model = BACKUP_MODEL,
                contents = prompt
            )
        except Exception as e:
            print("error: gemini 응답 오류")
            print(e)
            return
    text = response.text.strip()
    text = text.replace("```json", "").replace("```","")

    return json.loads(text)

   

if __name__ == "__main__":
    test = extract_concepts(
        "테스트 제목",
        """생성형 AI가 피싱 공격의 판을 바꾸고 있다.
        과거에는 어색한 문장이 필터 역할을 했지만,
        이제 공격자는 대상자의 직무·거래처·말투를 반영한
        맞춤형 메일을 자동으로 만들어낸다.

        QR코드로 가짜 로그인 페이지에 유도하고
        음성 딥페이크까지 결합하면,
        다중 인증도 우회가 가능해진다."""
        )
        
    print(test)
