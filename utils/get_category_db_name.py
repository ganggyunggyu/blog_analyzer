CATEGORY_SYSTEM_PROMPT = """
<system_instruction>
  <identity>
     당신은 키워드 카테고리 분류 전문가
  </identity>
  
  <core_principles>
    <principle_1>
      주어진 키워드를 분석해서 카테고리 목록에서 가장 적합한 것 하나만 선택
    </principle_1>
    
    <principle_2>
      카테고리 이름만 정확하게 반환 (설명, 부연 설명 일체 금지)
    </principle_2>
    
    <principle_3>
      목록에 없으면 "기타" 반환
    </principle_3>
    
    <principle_4>
      프롬프트에 카테고리가 명시되어 있으면 그걸 우선 반환
    </principle_4>
  </core_principles>
  
  <output_format>
    카테고리 이름 하나만 반환
    예: 미용학원
  </output_format>
</system_instruction>
"""


def build_category_prompt(keyword: str, categories: list[str]) -> str:
    """카테고리 분류용 프롬프트 생성"""

    categories_str = "\n".join([f"- {cat}" for cat in categories])

    return f"""
<task>
  <keyword>{keyword}</keyword>
  
  <categories>
{categories_str}
  </categories>
  
  <instruction>
    위 키워드가 어느 카테고리에 해당하는지 분석하고,
    카테고리 이름만 정확하게 반환하세요.
  </instruction>
</task>
"""


from _constants.Model import Model
from utils.ai_client_factory import call_ai

CATEGORIES = [
    "무지외반증",
    "마운자로",
    "다이어트",
    "다이어트보조제",
    "라미네이트",
    "멜라논크림",
    "브로멜라인",
    "anime",
    "서브웨이다이어트",
    "스위치온다이어트",
    "에리스리톨",
    "외국어교육_학원",
    "위고비",
    "미용학원",
    "족저근막염깔창",
    "캐리어",
    "파비플로라",
    "알파CD",
    "웨딩홀",
    "functional-food",
    "hospital",
    "home-appliances",
    "luxury",
    "애견동물_반려동물_분양",
    "맛집",
    "질분비물",
    "블록체인_가상화폐",
    "노래리뷰",
    "호텔",
    "영화리뷰",
    "김장",
    "공항_김포공항",
    "공항_인천공항",
    "정기청소",
]


async def get_category_db_name(keyword: str) -> str:
    """
    키워드를 분석하여 가장 적합한 카테고리 반환
    """
    try:
        category = call_ai(
            model_name=Model.GROK_4_RES,
            system_prompt=CATEGORY_SYSTEM_PROMPT,
            user_prompt=build_category_prompt(keyword, CATEGORIES),
        )

        return category if category in CATEGORIES else "기타"

    except Exception:
        return "기타"
