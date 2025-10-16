from __future__ import annotations
import re

from openai import OpenAI
from xai_sdk.chat import system as grok_system_message
from xai_sdk.chat import user as grok_user_message
from xai_sdk.search import SearchParameters

from config import GROK_API_KEY, OPENAI_API_KEY, grok_client
from _constants.Model import Model
from utils.query_parser import parse_query
from utils.text_cleaner import comprehensive_text_clean


model_name: str = Model.GPT5

if model_name.startswith("grok"):
    ai_service_type = "grok"
else:
    ai_service_type = "openai"

openai_client = OpenAI(api_key=OPENAI_API_KEY) if ai_service_type == "openai" else None

STORY_ANALYSIS_SYSTEM = """
유저가 보내는 원고를 토대로 이 작품의 줄거리와 등장인물 등 작품에 대한 내용을 아주 상세히 분석해야합니다
"""

USER_PROMPT_TEMPLATE = """
{keyword}
{note}
""".strip()


def story_analysis_gen(user_instructions: str, ref: str = "", category: str = "") -> str:
    if ai_service_type == "openai":
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY가 설정되어 있지 않습니다. .env를 확인하세요.")
    elif ai_service_type == "grok":
        if not GROK_API_KEY:
            raise ValueError("GROK_API_KEY가 설정되어 있지 않습니다. .env를 확인하세요.")

    parsed = parse_query(user_instructions)
    keyword = parsed.get("keyword", "")
    note = parsed.get("note", "")

    if not keyword:
        raise ValueError("키워드가 없습니다.")

    system = STORY_ANALYSIS_SYSTEM
    user = USER_PROMPT_TEMPLATE.format(keyword=keyword, note=note)

    if ai_service_type == "openai" and openai_client:
        response = openai_client.responses.create(
            model=model_name,
            instructions=system,
            input=user,
            reasoning={"effort": "medium"},
            text={"verbosity": "medium"},
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
        raise ValueError(f"AI 클라이언트를 찾을 수 없습니다. (service_type: {ai_service_type})")

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
