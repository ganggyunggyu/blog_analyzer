from __future__ import annotations
import re

from xai_sdk.chat import system as grok_system_message
from xai_sdk.chat import user as grok_user_message

from _prompts.service.get_mongo_prompt import get_mongo_prompt
from _prompts.system.ver1 import V1
from config import GROK_API_KEY, grok_client
from _constants.Model import Model
from utils.query_parser import parse_query
from utils.text_cleaner import comprehensive_text_clean

model_name: str = Model.GROK_4_NON_RES


def restaurant_grok_gen(
    user_instructions: str, ref: str = "", category: str = ""
) -> str:
    if not GROK_API_KEY:
        raise ValueError(
            "GROK_API_KEY가 설정되어 있지 않습니다. .env를 확인하세요."
        )

    parsed = parse_query(user_instructions)
    keyword, note = parsed.get("keyword", ""), parsed.get("note", "")

    if not keyword:
        raise ValueError("키워드가 없습니다.")

    mongo_data = get_mongo_prompt(category, user_instructions)

    system = f"""
# 역할 지침
당신은 맛집 투어를 즐기는 인플루언서 블로그 원고 작성 전문가입니다.

# 금지사항
- 마크다운 문법 금지

# 줄바꿈 이행
- 25~30자 사이에서 자연스러운 줄바꿈 필수

# 원고 작성 이행사항
{V1}
"""

    user = f"""
키워드: {keyword}

참조원고: {ref}
"""

    chat_session = grok_client.chat.create(model=model_name)
    chat_session.append(grok_system_message(system))
    chat_session.append(grok_user_message(user.strip()))
    response = chat_session.sample()

    text: str = getattr(response, "content", "") or ""

    text = comprehensive_text_clean(text)

    length_no_space = len(re.sub(r"\s+", "", text))
    print(f"원고 길이 체크: {length_no_space}")

    return text
