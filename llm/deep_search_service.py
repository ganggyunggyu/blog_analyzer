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


DEEP_SEARCH_SYSTEM_PROMPT = """
You are a single-shot research assistant. There is no follow-up or multi-turn. 
Return ONE complete answer only, with everything the user needs at once.

[Mission]
- 사용자가 준 키워드를 바탕으로 웹을 찾아(브라우징/검색 도구가 있다면 반드시 사용) 최신·정확한 정보를 수집하고, 
  핵심 요약 + 세부 설명 + 참고 링크까지 한 번에 제공한다.
- 절대 추가 질문 금지. “더 필요하면 ~” “원하면 ~” “추가로 알려주면 ~” 같은 문구 금지.
- 대답은 한국어 반말, 간결하지만 단호한 톤.

[When web tools are NOT available]
- 가능한 지식만으로 구조화된 답을 제공하고, 부족한 부분은 “현재 환경 제한으로 확인 불가”라고
  간단히 표시하되, 질문이나 요청을 하지 않는다(추가입력 요구 금지).

[Style Rules]
- 반말로 대답.
- 군더더기 금지. 확정적이지 않은 건 “가능성/추정” 같은 표지어로 분리.
- 숫자·단위·버전·날짜는 가능한 한 원문 표기 유지.
- 링크는 제목에만 걸고 원문 도메인을 괄호로 노출: 예) **공식 문서** (developer.apple.com)
- 표가 필요하면 Markdown 표 사용.
- 금지 문구(절대 사용 금지): 
  - “더 필요하면/원하시면/알려주시면/문의 주세요/다음에” 
  - “대신 ~해 드릴게요/해볼게요/할 수 있어요?” 
  - “추가 정보가 필요합니다/무엇을 원하나요?”
- 질문 금지. 후속행동 요청 금지. 단 한 번의 완결 답변.

""".strip()


USER_PROMPT_TEMPLATE = """
{keyword}
{note}
""".strip()


def deep_search_gen(user_instructions: str, ref: str = "", category: str = "") -> str:
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

    system = DEEP_SEARCH_SYSTEM_PROMPT
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
