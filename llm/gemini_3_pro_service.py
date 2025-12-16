from __future__ import annotations
import re
import time

from anthropic import Anthropic
from openai import OpenAI
from xai_sdk.chat import system as grok_system_message
from xai_sdk.chat import user as grok_user_message
from _prompts.service.get_mongo_prompt import get_mongo_prompt
from _prompts.service.get_category_tone_rules import get_category_tone_rules
from _prompts.system import claude_system
from _prompts.system.grok_system import get_grok_system_prompt
from _prompts.system.ver1 import V1
from config import (
    CLAUDE_API_KEY,
    GEMINI_API_KEY,
    GROK_API_KEY,
    OPENAI_API_KEY,
    UPSTAGE_API_KEY,
)
from _constants.Model import Model
from utils.query_parser import parse_query
from utils.text_cleaner import comprehensive_text_clean

from google import genai
from google.genai import types

from _prompts.rules.human_writing_style import human_writing_rule
from _prompts.rules.line_example_rule import line_example_rule
from _prompts.rules.line_break_rules import line_break_rules


model_name: str = Model.GEMINI_3_PRO


if model_name.startswith("gemini"):
    ai_service_type = "gemini"
elif model_name.startswith("claude"):
    ai_service_type = "claude"
elif model_name.startswith("solar"):
    ai_service_type = "solar"
elif model_name.startswith("grok"):
    ai_service_type = "grok"
else:
    ai_service_type = "openai"


openai_client = OpenAI(api_key=OPENAI_API_KEY) if ai_service_type == "openai" else None
gemini_client = (
    genai.Client(api_key=GEMINI_API_KEY) if ai_service_type == "gemini" else None
)
claude_client = (
    Anthropic(api_key=CLAUDE_API_KEY) if ai_service_type == "claude" else None
)


def gemini_3_pro_gen(user_instructions: str, ref: str = "", category: str = "") -> str:
    if ai_service_type == "solar":
        if not UPSTAGE_API_KEY:
            raise ValueError("UPSTAGE_API_KEY가 설정되어 있지 않습니다.")
    elif ai_service_type == "gemini":
        if not GEMINI_API_KEY:
            raise ValueError(
                "GEMINI_API_KEY가 설정되어 있지 않습니다. .env를 확인하세요."
            )
    elif ai_service_type == "openai":
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
    keyword, note = parsed.get("keyword", ""), parsed.get("note", "")

    if not keyword:
        raise ValueError("키워드가 없습니다.")
    mongo_data = get_mongo_prompt(category, user_instructions)
    grok_system = get_grok_system_prompt(
        keyword=keyword,
        category=category,
    )

    system = claude_system.get_claude_system_prompt(
        category=category,
        mongo_data=mongo_data,
    )

    user = f"""
    키워드: {keyword}

    추가 요청: {note}

    참조 원고: {ref}

{V1}
    """.strip()

    if ai_service_type == "gemini" and gemini_client:
        response = gemini_client.models.generate_content(
            model=model_name,
            config=types.GenerateContentConfig(
                system_instruction=grok_system,
            ),
            contents=user,
        )
    else:
        raise ValueError(
            f"AI 클라이언트를 찾을 수 없습니다. (service_type: {ai_service_type})"
        )

    if ai_service_type == "gemini":
        text: str = getattr(response, "text", "") or ""
    elif ai_service_type == "openai":
        text: str = getattr(response, "output_text", "") or ""
    elif ai_service_type == "solar":
        choices = getattr(response, "choices", []) or []
        if not choices or not getattr(choices[0], "message", None):
            raise RuntimeError("SOLAR가 유효한 choices/message를 반환하지 않았습니다.")
        text: str = (choices[0].message.content or "").strip()
    elif ai_service_type == "claude":
        content_blocks = getattr(response, "content", [])
        text: str = getattr(content_blocks[0], "text", "") if content_blocks else ""
    elif ai_service_type == "grok":
        text = getattr(response, "content", "") or ""
    else:
        text: str = ""
    text = comprehensive_text_clean(text)

    length_no_space = len(re.sub(r"\s+", "", text))
    print(f"원고 길이 체크: {length_no_space}")

    return text
