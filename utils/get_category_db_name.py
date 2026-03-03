from _constants.Model import Model
from _constants.categories import CATEGORIES
from utils.ai_client_factory import call_ai

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

    <principle_5>
      안과/치과처럼 혼동되기 쉬운 의료 키워드는 시술 대상 부위 기준으로 구분
      - 눈, 시력교정, 각막, 렌즈삽입, 백내장 관련이면 반드시 "안과"
      - 치아, 잇몸, 치과 시술 관련이면 "라미네이트" 우선 검토
    </principle_5>
  </core_principles>

  <output_format>
    카테고리 이름 하나만 반환
    예: 미용학원
  </output_format>
</system_instruction>
"""


def build_category_prompt(keyword: str) -> str:
    """카테고리 분류용 프롬프트 생성"""

    categories_str = "\n".join([f"- {cat}" for cat in CATEGORIES])

    return f"""
<task>
  <keyword>{keyword}</keyword>
  
  <categories>
{categories_str}
  </categories>

  <disambiguation_guide>
    안과 시술 예시:
    - 라식, 라섹, 투데이라섹, 스마일라식, 스마일프로
    - 렌즈삽입술, ICL, 백내장수술, 노안교정, 드림렌즈
    - 안구건조증 치료, 시력교정, 각막/망막/안압 검사

    치과 시술 예시:
    - 라미네이트, 치아미백, 치아교정, 임플란트
    - 충치치료, 신경치료, 잇몸치료, 스케일링

    중요 구분:
    - "라섹"은 치과가 아니라 안과 시술
    - 키워드가 안과 시력교정 문맥이면 "안과"를 반환
    - 키워드가 치과/치아 미용 문맥이면 "라미네이트"를 우선 검토
  </disambiguation_guide>
  
  <instruction>
    위 키워드가 어느 카테고리에 해당하는지 분석하고,
    카테고리 이름만 정확하게 반환하세요.
  </instruction>
</task>
"""


async def get_category_db_name(keyword: str) -> str:
    """
    키워드를 분석하여 가장 적합한 카테고리 반환
    """
    try:
        category = call_ai(
            model_name=Model.GROK_4_1_NON_RES,
            system_prompt=CATEGORY_SYSTEM_PROMPT,
            user_prompt=build_category_prompt(keyword),
        )

        return category if category in CATEGORIES else "기타"

    except Exception:
        return "기타"
