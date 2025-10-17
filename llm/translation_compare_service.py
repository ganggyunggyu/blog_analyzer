from __future__ import annotations
import re
import time

from openai import OpenAI
from xai_sdk.chat import system as grok_system_message
from xai_sdk.chat import user as grok_user_message
from xai_sdk.search import SearchParameters

from config import (
    GROK_API_KEY,
    OPENAI_API_KEY,
    grok_client,
)
from _constants.Model import Model
from utils.query_parser import parse_query
from utils.text_cleaner import comprehensive_text_clean


model_name: str = Model.GPT5


if model_name.startswith("grok"):
    ai_service_type = "grok"
else:
    ai_service_type = "openai"


openai_client = OpenAI(api_key=OPENAI_API_KEY) if ai_service_type == "openai" else None


TRANSLATION_COMPARE_SYSTEM_PROMPT = """
너는 문학 전문 어시스턴트야. 사용자가 책의 한국어 번역본 여러 개를 비교해 문체를 보고 구매 결정을 돕도록 해.

입력 형식: "[작가] - [도서 명]"

출력 형식 (Markdown):
- **번역본 1**
  - 번역가: ○○
  - 출판사: ○○ (연도)
  - 발췌 문장: "……(번역된 문장, 문체 비교 목적)"
- **번역본 2**
  - (위와 동일 형식)
- (주요 번역본 나열)

조건:
1. 동일 원문 구절(예: 서두나 상징적 문장)에서 발췌해 문체 차이(어휘, 리듬, 뉘앙스) 비교 쉽게 해.
2. 저작권 위해 인용 수준만.
3. 출처 반드시 명시 (예: "출처: 교보문고 DB, 2020년 판본" – 신뢰할 수 있는 도서 DB, 위키피디아, 서점 사이트 기반으로 확인).
4. 정보 없거나 확인 불가 시: "이 책의 한국어 번역본 정보를 찾을 수 없어요. 더 구체적인 제목이나 판본을 알려주세요."라고 솔직히 말해.
5. 객관적으로: 문체 평가나 추천은 하지 말고, 사실만 제시 (사용자가 직접 비교하게).

예시 입력:
헤르만 헤세 - 시든 잎사귀

→ 출력 예시:

**번역본 1**
- 번역가: 김연경
- 출판사: 문학동네 (2005)
- 발췌 문장: "가을 바람이 불어오면 잎사귀들은 조용히 떨어지네, 마치 인생의 무상함을 속삭이듯."
  (출처: 교보문고 DB, 2005년 판본)

**번역본 2**
- 번역가: 이재룡
- 출판사: 창비 (2018)
- 발췌 문장: "바람에 흩날리는 낙엽처럼, 우리의 삶은 스러지기 마련이다."
  (출처: 예스24 서점 정보, 2018년 개정판)

**번역본 3**
- 번역가: 박성원
- 출판사: 민음사 (1992)
- 발췌 문장: "서늘한 가을기운 속에, 잎들이 땅으로 스러지는 광경은 영원한 이별을 연상시킨다."
  (출처: 나무위키 및 알라딘 도서 DB, 1992년 초판)


- 금지 문구(절대 사용 금지):
  - "더 필요하면/원하시면/알려주시면/문의 주세요/다음에"
  - "대신 ~해 드릴게요/해볼게요/할 수 있어요?"
  - "추가 정보가 필요합니다/무엇을 원하나요?"
- 질문 금지. 후속행동 요청 금지. 단 한 번의 완결 답변.
""".strip()

USER_PROMPT_TEMPLATE = """
{keyword}
{note}
""".strip()


def translation_compare_gen(user_instructions: str, ref: str = "", category: str = "") -> str:
    if ai_service_type == "openai":
        if not OPENAI_API_KEY:
            raise ValueError(
                "OPENAI_API_KEY가 설정되어 있지 않습니다. .env를 확인하세요."
            )
    elif ai_service_type == "grok":
        if not GROK_API_KEY:
            raise ValueError(
                "GROK_API_KEY가 설정되어 있지 않습니다. .env를 확인하세요."
            )

    parsed = parse_query(user_instructions)
    keyword = parsed.get("keyword", "")
    note = parsed.get("note", "")

    if not keyword:
        raise ValueError("키워드가 없습니다.")

    system = TRANSLATION_COMPARE_SYSTEM_PROMPT
    user = USER_PROMPT_TEMPLATE.format(keyword=keyword, note=note)

    if ai_service_type == "openai" and openai_client:
        response = openai_client.responses.create(
            model=model_name,
            instructions=system,
            input=user,
            reasoning={"effort": "medium"},
            text={"verbosity": "medium"},
            tools=[{"type": "web_search"}],
        )
    elif ai_service_type == "grok" and grok_client:
        chat_session = grok_client.chat.create(
            model=model_name,
            search_parameters=SearchParameters(mode="auto"),
        )
        chat_session.append(grok_system_message(system))
        chat_session.append(grok_user_message(user))
        response = chat_session.sample()
    else:
        raise ValueError(
            f"AI 클라이언트를 찾을 수 없습니다. (service_type: {ai_service_type})"
        )

    if ai_service_type == "openai":
        text: str = getattr(response, "output_text", "") or ""
    elif ai_service_type == "grok":
        text = getattr(response, "content", "") or ""
    else:
        text: str = ""

    text = comprehensive_text_clean(text)

    length_no_space = len(re.sub(r"\s+", "", text))
    print(f"원고 길이 체크: {length_no_space}")

    return text
