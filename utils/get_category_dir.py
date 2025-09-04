"""
키워드 기반 카테고리 매핑 유틸리티 (AI 방식 + 동적 폴더 검색)
"""

import os
from openai import OpenAI
from _constants.Model import Model
from config import OPENAI_API_KEY


def get_data_folder_categories() -> list[str]:
    """
    _data 폴더에서 실제 카테고리 폴더명들을 동적으로 가져오기
    """
    data_folder = "_data"

    if not os.path.exists(data_folder):

        return []

    categories = []
    for item in os.listdir(data_folder):
        item_path = os.path.join(data_folder, item)

        if os.path.isdir(item_path) and not item.startswith("."):
            categories.append(item)
    print(categories)
    return sorted(categories)


def get_category_dict() -> dict[str, str]:
    """
    실제 폴더명 목록 반환 (더 이상 사용하지 않음)
    """
    return {}


def categorize_keyword_with_ai_fixed(keyword: str) -> str:
    """
    AI가 키워드를 분석해서 직접 폴더명으로 리턴 (동적 폴더 리스트 사용)
    """

    folder_categories = get_data_folder_categories()

    if not folder_categories or not OPENAI_API_KEY:

        return folder_categories[0] if folder_categories else "영양제_건강보조식품"

    client = OpenAI(api_key=OPENAI_API_KEY)

    prompt = f"""
    다음 키워드가 어떤 카테고리에 가장 적합한지 아래 폴더 목록에서 하나만 골라주세요.
    - 라미네이트: 치과
    - 스마일라식: 안과
    - 인천공항택시: 
    다른 설명 없이 폴더명만 정확하게 반환해야 합니다.
    어떻게든 연관점을 찾아서 반환해야합니다.

    [키워드]
    {keyword}

    [폴더 카테고리 목록]
    {', '.join(folder_categories)}
    """

    try:
        response = client.chat.completions.create(
            model=Model.GPT5_MINI,
            messages=[
                {
                    "role": "system",
                    "content": "You are a keyword categorization expert.",
                },
                {"role": "user", "content": prompt},
            ],
        )

        content = response.choices[0].message.content
        print(content)
        if content is None:
            return (
                folder_categories[0] if folder_categories else "01_영양제_건강보조식품"
            )

        ai_category = content.strip()

        if ai_category in folder_categories:
            return ai_category
        else:

            return (
                folder_categories[0] if folder_categories else "01_영양제_건강보조식품"
            )

    except Exception as e:
        print(f"AI 카테고리 분석 실패: {e}")
        return folder_categories[0] if folder_categories else "영양제_건강보조식품"


def get_category_by_keyword(keyword: str) -> str:
    """
    키워드를 AI로 분석해서 해당하는 카테고리 폴더를 반환
    """
    return categorize_keyword_with_ai_fixed(keyword)
