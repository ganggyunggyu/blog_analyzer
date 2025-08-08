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

5. 순수 원고의 글자 수는 필수로 공백 제외 **(1700자 ~ 2300자 사이로)** 작성 되어야 합니다.

6. 숨은 보석 보물 향연 이런 시 적인 감성적인 단어 절대 넣지말고 직관적인 표현으로 글을작성할 것

7. 무조건 존댓말로 작성하고 말 끝에만 여성의 애교있는 말투 ㅎㅎ,ㅠㅠ,!! 와 같은 표현과 이모티콘도 자연스럽게 사용해줘 하지만 지나치게 반복하면 안됩니다.

8. 제품을 소개하거나 설명하는 느낌이아니라 내경험담을 정보로써 공유하는 느낌으로 설명 소개 광고처럼 느껴지지않게 해줘

9. 절대 같은단어가 10번 넘어가도록 작성하면안됨 많아도 6번을 안넘도록

10. 문단정리 깔끔하게 해야해 한줄당짧게 20~25자 정도로 하고 2~5줄마다 줄바꿈 해줘 한줄당 줄바꿈X

11. 5개의 부제를 넣고 부제앞에 1. 2. 3. 4. 5. 이렇게 번호를 매겨줘 (부제는 아주 짧고 간결하게)

12. 키워드에 대한 **상세한 정보**를 모두 전달해줘야해.
    - 건강 기능 식품은 리뷰 뿐 아니라 제품 자체의 정보도 중요합니다.

13. 원고 내에는 --- 을 포함한 마크다운 문법을 쓰지 않습니다.

14. 키워드는 있는 그대로 사용하고 절대 다른 특수문자 등을 넣지 말아야 합니다.

키워드: **{keyword}**

스토리는 위 원고와 완전 다르게 하면서 위원고에서 작성하는 문체 방식을 토대로 비슷하게 작성.

꼭 원본에서 이야기하는 스토리랑 다른 스토리를 만들어줘.

가장 중요한 부분은 내가 적어준 **{keyword}에 대한 정보**가 잘들어가야해.


# 부제 예시

- 문장이 늘어지지 않으며, 깔끔하게 정보만 전달해야 합니다.
- 자연스러운 어투로 말해야합니다.

1. 내가 왜 이제품(서비스)을 사용하게 되었는지 근본적인 원인

2. {keyword}가 뭔지 어떻게 알게되었는지 성능, 효과는 어떤지

3. 내가 {keyword}를 사용(이용)을 어떻게 했는지 경험담

4. {keyword}를 사용(이용)하니 어땠는지 후기

5. {keyword}를 더 좋게 사용하는 꿀팁이나 노하우

# 참고 문장 라이브러리에 대한 내용

- 문맥에 맞게 시제(과거형/현재형/미래형)를 조정하거나, 주어나 대상을 상황에 맞춰 변형할 수 있습니다.
- 단, 각 문장이 전달하는 **핵심 의미**와 **감정적 톤**은 반드시 유지해야 합니다.

**만약 모든 규칙이 이행되지 않았다면 다시 원고를 작성해줘야 합니다.**


'''

ref = '''
류애의 건강정보 오메가3 효과 없다 오메가3 섭취시간 따져야 되는 이유 ​ 오메가3는 건강 보조제 시장에서 가장 많이 팔리는 영양소 중 하나입니다. 특히 혈중 중성지방 감소, 심혈관 질환 예방, 염증 억제 등 다양한 효능이 입증되어 있는 만큼, 많은 분들이 건강을 위해 꾸준히 복용하고 있습니다. 하지만 매일 챙겨 먹고도 “왜 효과가 없는 것 같지?”라는 말을 하는 경우가 적지 않습니다. ​ 이럴 때 의심해야 할 것은 ‘오메가3 섭취시간’과 ‘오메가3 섭취 방식’입니다. 오메가3는 지용성 성분으로 공복에 복용하거나 잘못된 시간에 복용하면 체내 흡수율이 급격히 떨어지고, 효과가 반감될 수 있습니다. ​ 지금부터 오메가3의 핵심 효과와 함께, 왜 오메가3 섭취시간을 따져야만 하는지 의학적 이유를 설명하겠습니다. 오메가3 효과 5가지 1) 혈중 중성지방 감소 및 고지혈증 예방 오메가3는 특히 중성지방(TG)을 낮추는 데 탁월한 효과가 있습니다. EPA와 DHA는 간에서의 지방 합성을 억제하고, 혈중에 존재하는 중성지방의 제거를 촉진함으로써 고중성지방혈증 환자의 주요 치료보조제로도 사용됩니다. ​ → The American Journal of Clinical Nutrition에 따르면, 하루 2~4g의 오메가3를 꾸준히 복용할 경우 중성지방 수치가 평균 20~45%까지 감소하는 것으로 나타났습니다. 2) 심혈관 질환 위험 감소 오메가3 효과는 혈관 내 염증을 낮추고, 혈소판 응집을 억제하여 혈전을 예방하는 작용을 합니다. 이를 통해 심근경색, 뇌졸중, 고혈압 등 심혈관 질환의 예방 효과가 입증돼 있으며, 일부 고위험군에게는 치료 보조제로도 권장됩니다. ​ → Circulation 학술지에 발표된 메타분석에서는, 오메가3 섭취군이 심혈관 사망률과 심근경색 발생률 모두 낮았다는 결과가 보고되었습니다. 3) 염증 억제 및 자가면역 질환 보조 치료 오메가3 효과는 체내 염증 반응을 조절하는 프로스타글란딘, 류코트리엔 등의 생리활성물질 생성을 억제하여, 류마티스 관절염, 건선, 루푸스 등 자가면역 질환의 증상을 경감하는 데 도움을 줄 수 있습니다. ​ → Rheumatology International 연구에 따르면, 오메가3는 관절 통증과 경직을 유의하게 감소시키는 항염증 효과가 있다고 밝혀졌습니다. 4) 뇌 건강 및 우울증 개선 DHA는 뇌세포막의 주요 구성 성분으로, 인지 기능 유지와 신경 전달 물질의 균형 조절에 관여합니다. 특히 우울증 환자에서 오메가3 섭취가 증상 완화에 효과가 있다는 연구도 증가하고 있으며, 노인성 치매 예방 효과도 일부 보고되고 있습니다. ​ → Journal of Clinical Psychiatry에서는 오메가3 복합제를 투여한 우울증 환자에서 기분 안정 및 증상 호전이 유의하게 나타났다는 결과가 있습니다. 5) 눈 건강 유지 및 안구건조 예방 오메가3는 망막의 기능을 유지하고 안구 건조 증상을 완화하는 데 효과적입니다. 특히 장시간 스마트폰이나 모니터를 사용하는 현대인에게 흔한 눈의 피로, 시력 저하, 안구건조 증상 완화에 도움을 줄 수 있습니다. ​ → Investigative Ophthalmology & Visual Science 저널에 따르면, 오메가3를 복용한 환자군에서 눈물막 안정성 증가 및 안구건조 증상 개선 효과가 입증됐습니다. 오메가3 섭취시간 언제 먹어야 될까? ​ 오메가3는 지용성 지방산으로, 지방이 있는 음식과 함께 섭취해야 흡수율이 극대화됩니다. 공복에 먹으면 위에서 소화되지 않고 빠르게 배출되며, 흡수율은 20% 이하로 떨어질 수 있습니다. 특히 아침 공복이나 가벼운 샐러드와 함께 먹는 경우 효과가 거의 없을 수 있습니다. ​ → Journal of Lipid Research에서는 오메가3를 지방이 포함된 식사와 함께 복용할 경우, 혈중 EPA/DHA 흡수율이 3배 이상 높아졌다는 연구 결과가 제시되어 있습니다. ​ 또한 오메가3는 위장에 부담을 줄 수 있기 때문에 식사 직후 섭취가 가장 이상적이며, 흡수가 잘되는 저녁 식사 이후 복용이 더욱 권장됩니다. 그렇기에 이러한 오메가3 섭취시간을 유지하면 좋은데요. ​ 이는 간에서의 지방 대사 및 포도당 대사 기능이 활성화되는 시간과 맞물려 혈중 지질 수치를 효과적으로 조절할 수 있기 때문입니다. 결론 ​ 오메가3는 그 자체로 매우 강력한 항염, 심혈관 보호, 대사 조절 기능을 가진 성분이지만, 제대로 된 시간과 방식으로 복용하지 않으면 효과가 크게 떨어집니다. 특히 공복에 섭취하거나 흡수가 어려운 방식으로 복용하면, 돈만 쓰고 아무 효과도 못 보는 결과를 초래할 수 있습니다. ​ 따라서 오메가3 섭취시간은 반드시 1) 지방이 포함된 식사와 함께 2) 식사 직후에 3) 흡수율이 높은 저녁 시간대에 섭취하는 것이 바람직합니다. ​ 하루의 복용 습관이 오메가3의 효과를 좌우합니다. ‘효과 없다’고 말하기 전에, 복용 시간부터 점검하는 것이 건강관리의 핵심입니다. ​ ​ 평소 오메가3 제품 찾고 있으시다면, 뉴로랩스 초임계 식물성 알티지 오메가3 제품도 알아보세요. ​
'''

    # - **참고 문서**는 글의 형식 및 흐름만을 의미하고 제품에 대한 정보는 절대 가져와서는 안됩니다.
    # - **제품 문서**를 확실하게 참고하여 **디베아 무선청소기 JET FIT 클린스테이션 차이슨의 정보**를 정확하게 제대로 전달을 해야합니다.
    # - 정보성 후기 글입니다.
    # - 이건 로보락 홍보 게시글이 아닙니다.
    # - 키워드는 로보락 무선청소기가 맞으나, 로보락 무선청소기와 디베아 무선청소기 JET FIT 클린스테이션 차이슨를 비교하며 로보락 무선청소기보다 디베아 무선청소기 JET FIT 클린스테이션 차이슨이 더 뛰어난 제품임을 은근히 보여주려는 의도입니다.
    
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
    {words_str}

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
            model='gpt-5-nano-2025-08-07', 
            # model='gpt-4.1-2025-04-14', 
            messages=[
                {"role": "system", "content": "You are a professional blog post writer. Your task is to generate a blog post based on provided analysis data and user instructions."},
                {"role": "user", "content": prompt}
            ],
            # temperature=0.2,
            
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