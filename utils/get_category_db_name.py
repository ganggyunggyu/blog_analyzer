from openai import OpenAI
from _constants import Model
from config import OPENAI_API_KEY

categories = [
    "공항_장기주차장:주차대행",
    "다이어트",
    "다이어트보조제",
    "라미네이트",
    "마운자로가격",
    "마운자로처방",
    "멜라논크림",
    "anime",
    "서브웨이다이어트",
    "스위치온다이어트",
    "에리스리톨",
    "외국어교육_학원",
    "위고비",
    # "위고비부작용",
    # "위고비후기",
    # "위고비처방",
    "족저근막염깔창",
    "캐리어",
    "파비플로라",
    "알파CD",
    "beauty-products",
    "beauty-treatment",
    "dentistry",
    "edu",
    "e-ciga-liquid",
    "functional-food",
    "hospital",
    "home-appliances",
    "legalese",
    "luxury",
    "melatonin",
    "ophthalmology",
    "애견동물_반려동물_분양",
    "restaurant",
    "startup",
    "wedding",
    "맛집",
]


def get_category_db_name_sync(keyword: str) -> str:
    """
    주어진 키워드를 AI를 사용하여 분석하고, 가장 적합한 카테고리를 반환합니다. (동기 버전)
    """
    if not OPENAI_API_KEY:
        raise ValueError(
            "API 키가 설정되지 않았습니다. .env 파일에 OPENAI_API_KEY를 추가해주세요."
        )
    client = OpenAI(api_key=OPENAI_API_KEY)

    prompt = f"""
    다음 키워드가 어떤 카테고리에 가장 적합한지 아래 목록에서 하나만 골라주세요.
    다른 설명 없이 카테고리 이름만 정확하게 반환해야 합니다.
    프롬프트에 카테고리 언급이 있다면 그것을 기반으로 반환해야합니다.


    [키워드]
    {keyword}

    [카테고리 목록]
    {categories}

    ***반드시 가장 유사한걸 하나라도 반환해야합니다.***
    """

    try:
        response = client.chat.completions.create(
            model=Model.Model.GPT4_1,
            messages=[
                {
                    "role": "system",
                    "content": "You are a keyword categorization expert.",
                },
                {"role": "user", "content": prompt},
            ],
        )
        content = response.choices[0].message.content
        if content == None:
            raise
        category = content.strip()

        if category not in categories:
            return "기타"

        return category

    except Exception:
        return "기타"


async def get_category_db_name(keyword: str) -> str:
    """
    주어진 키워드를 AI를 사용하여 분석하고, 가장 적합한 카테고리를 반환합니다.
    """
    if not OPENAI_API_KEY:
        raise ValueError(
            "API 키가 설정되지 않았습니다. .env 파일에 OPENAI_API_KEY를 추가해주세요."
        )
    client = OpenAI(api_key=OPENAI_API_KEY)

    prompt = f"""
    다음 키워드가 어떤 카테고리에 가장 적합한지 아래 목록에서 하나만 골라주세요.
    다른 설명 없이 카테고리 이름만 정확하게 반환해야 합니다.    
    프롬프트에 카테고리 언급이 있다면 그것을 기반으로 반환해야합니다.
    

    [키워드]
    {keyword}

    [카테고리 목록]
    {categories}

    ***반드시 가장 유사한걸 하나라도 반환해야합니다.***
    """

    try:
        response = client.chat.completions.create(
            model=Model.Model.GPT4_1,
            messages=[
                {
                    "role": "system",
                    "content": "You are a keyword categorization expert.",
                },
                {"role": "user", "content": prompt},
            ],
        )
        content = response.choices[0].message.content
        if content == None:
            raise
        category = content.strip()

        if category not in categories:
            return "기타"

        return category

    except Exception:
        return "기타"
