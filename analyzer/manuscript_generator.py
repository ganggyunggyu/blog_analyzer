import os
from openai import OpenAI
import json
from config import OPENAI_API_KEY
from mongodb_service import MongoDBService
import time


def getKoPrompt(keyword: str): 

    return '''
---
**반드시 참고 문서의 어투 및 흐름을 참고하여 작업할 것**

# 핵심 규칙

글을 작성하는 방식 단어 문장흐름 문체 형태소 등을 참고하라고 넣은 원고이기 때문에 무조건 스토리가 달라야해

그리고 글을 제발 비슷한 문장 문구 글 반복해서 작성하지마 했던 얘기 또 하는거 싫어

네이버 블로그니까 원고에 마크다운 문법 사용하지말아야해.

1. 실제로 겪어본 사람들만 알수있는 정보 위주로 작성 모든 정보는 디테일 하게 작성한다.

2. 같은말과 비슷한 단어를 자주 사용하지 말고 새로운 단어와 말을 섞어서 반복되는 문장 단어 형태소가 나오지않게끔 잘 조절할 것

3. 키워드를 검색하는사람들이 궁금해 할만한 항목과 연관 단어(형태소)를 사용해서 작성할 것

4. 와,진짜,정말 <<이런 감탄사나 강조부사를 넣지 않아야 합니다.

5. 순수 원고의 글자 수는 필수로 공백 제외 **(3000단어)** 이상 작성 되어야 합니다.

6. 숨은 보석 보물 향연 이런 시 적인 감성적인 단어 절대 넣지말고 직관적인 표현으로 글을작성할 것

7. 무조건 존댓말로 작성하고 말 끝에만 여성의 애교있는 말투 ㅎㅎ,ㅠㅠ,!! 와 같은 표현과 이모티콘도 자연스럽게 사용해줘

8. 제품을 소개하거나 설명하는 느낌이아니라 내경험담을 정보로써 공유하는 느낌으로 설명 소개 광고처럼 느껴지지않게 해줘

9. 절대 같은단어가 10번 넘어가도록 작성하면안됨 많아도 6번을 안넘도록

10. 문단정리 깔끔하게 해야해 한줄당짧게 20~25자 정도로 하고 2~5줄마다 줄바꿈 해줘 한줄당 줄바꿈X

11. 5개의 부제를 넣고 부제앞에 1. 2. 3. 4. 5. 이렇게 번호를 매겨줘 (부제는 아주 짧고 간결하게)

12. 키워드에 대한 **상세한 정보**를 모두 전달해줘야해.
    - 건강 기능 식품은 리뷰 뿐 아니라 제품 자체의 정보도 중요합니다.

13. 원고 내에는 --- 을 포함한 마크다운 문법을 쓰지 않습니다.

키워드: **{keyword}**

스토리는 위 원고와 완전 다르게 하면서 위원고에서 작성하는 문체 방식을 토대로 비슷하게 작성.

꼭 원본에서 이야기하는 스토리랑 다른 스토리를 만들어줘.

가장 중요한 부분은 내가 적어준 **{keyword}에 대한 정보**가 잘들어가야해.


# 부제 예시

- 문장이 늘어지지 않으며, 심플하고 깔끔하게 정보만 전달해야 합니다.

1. 내가 왜 이제품(서비스)을 사용하게 되었는지 근본적인 원인

2. {keyword}가 뭔지 어떻게 알게되었는지 성능,효과 등 은 어떤지

3. 내가 {keyword}를 사용(이용)을 어떻게 했는지 경험담

4. {keyword}를 사용(이용)하니 어땠는지 후기

5. {keyword}를 더 좋게 사용하는 꿀팁이나 노하우 등

# 참고 문장 라이브러리에 대한 내용

- 문맥에 맞게 시제(과거형/현재형/미래형)를 조정하거나, 주어나 대상을 상황에 맞춰 변형할 수 있습니다.
- 단, 각 문장이 전달하는 **핵심 의미**와 **감정적 톤**은 반드시 유지해야 합니다.

**만약 모든 규칙이 이행되지 않았다면 다시 원고를 작성해줘야 합니다.**


'''

ref = '''

'''

    # - **참고 문서**는 글의 형식 및 흐름만을 의미하고 제품에 대한 정보는 절대 가져와서는 안됩니다.
    # - **제품 문서**를 확실하게 참고하여 **디베아 무선청소기 JET FIT 클린스테이션 차이슨의 정보**를 정확하게 제대로 전달을 해야합니다.
    # - 정보성 후기 글입니다.
    # - 이건 로보락 홍보 게시글이 아닙니다.
    # - 키워드는 로보락 무선청소기가 맞으나, 로보락 무선청소기와 디베아 무선청소기 JET FIT 클린스테이션 차이슨를 비교하며 로보락 무선청소기보다 디베아 무선청소기 JET FIT 클린스테이션 차이슨이 더 뛰어난 제품임을 은근히 보여주려는 의도입니다.
    
    # {words_str}
    # - 위 지침을 반드시 지켜주세요.
def generate_manuscript_with_ai(
    unique_words: list,
    sentences: list,
    expressions: dict,
    parameters: dict,
    user_instructions: str
) -> str:
    """
    수집된 분석 데이터를 기반으로 OpenAI API를 사용하여 블로그 원고를 생성합니다.
    """
    if not OPENAI_API_KEY:
        raise ValueError("API 키가 설정되지 않았습니다. .env 파일에 OPENAI_API_KEY를 추가해주세요.")
    client = OpenAI(api_key=OPENAI_API_KEY)

    
    # 데이터를 프롬프트에 포함하기 위해 문자열로 변환
    words_str = ", ".join(unique_words) if unique_words else "없음"
    sentences_str = "\n- ".join(sentences) if sentences else "없음"
    expressions_str = json.dumps(expressions, ensure_ascii=False, indent=2) if expressions else "없음"
    parameters_str = json.dumps(parameters, ensure_ascii=False, indent=2) if parameters else "없음"




    prompt = f"""

    [고유 단어 리스트]

    [문장 리스트]
     - {sentences_str}
    
    [표현 라이브러리 (중분류 키워드: [표현])]
    {expressions_str}

    [AI 개체 인식 및 그룹화 결과 (대표 키워드: [개체])]
    {parameters_str}

    [사용자 지시사항]
    {user_instructions}

    [참고 문서]
    {ref}

    [요청]

    {getKoPrompt(keyword=user_instructions)}

    """

    try:
        response = client.chat.completions.create(
            model='gpt-4.1-2025-04-14', 
            messages=[
                {"role": "system", "content": "You are a professional blog post writer. Your task is to generate a blog post based on provided analysis data and user instructions."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            
        )
        usage = response.usage
        print(f"사용된 토큰 수 - prompt: {usage.prompt_tokens}, completion: {usage.completion_tokens}, total: {usage.total_tokens}")

        generated_manuscript = response.choices[0].message.content.strip()

        return generated_manuscript
    except Exception as e:
        print(f"OpenAI API 호출 중 오류가 발생했습니다: {e}")
        return 
    

    

    # gpt-4.1-2025-04-14

def categorize_keyword_with_ai(keyword: str) -> str:
    """
    주어진 키워드를 AI를 사용하여 분석하고, 가장 적합한 카테고리를 반환합니다.
    """
    if not OPENAI_API_KEY:
        raise ValueError("API 키가 설정되지 않았습니다. .env 파일에 OPENAI_API_KEY를 추가해주세요.")
    client = OpenAI(api_key=OPENAI_API_KEY)

    # 카테고리 목록 예시입니다. 필요에 따라 수정하거나 확장할 수 있습니다.
    categories = [
        "hospital", "legalese", "beauty-treatment", "functional-food", 
        "startup", "home-appliances"
    ]

    prompt = f"""
    다음 키워드가 어떤 카테고리에 가장 적합한지 아래 목록에서 하나만 골라주세요.
    다른 설명 없이 카테고리 이름만 정확하게 반환해야 합니다.

    [키워드]
    {keyword}

    [카테고리 목록]
    {', '.join(categories)}
    """

    try:
        response = client.chat.completions.create(
            model='gpt-4.1-mini-2025-04-14',
            messages=[
                {"role": "system", "content": "You are a keyword categorization expert."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0,
        )
        
        category = response.choices[0].message.content.strip()
        
        # AI가 목록에 없는 답변을 할 경우를 대비한 안전장치
        if category not in categories:
            return "기타"
            
        return category

    except Exception as e:
        print(f"OpenAI API 호출 중 오류가 발생했습니다: {e}")
        return "기타" # 오류 발생 시 기본값 반환