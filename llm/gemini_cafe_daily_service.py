"""Gemini Cafe Daily - 카페 일상 글 생성 서비스 (900~1100자)"""

from __future__ import annotations

from _prompts.gemini.cafe_daily_system import get_gemini_cafe_daily_system_prompt
from _prompts.gemini.cafe_daily_user import get_gemini_cafe_daily_user_prompt
from _prompts.comment import get_random_persona
from _constants.Model import Model
from utils.query_parser import parse_query
from utils.text_cleaner import comprehensive_text_clean
from utils.ai_client_factory import call_ai


MODEL_NAME: str = Model.GEMINI_3_FLASH_PREVIEW


def gemini_cafe_daily_gen(user_instructions: str, category: str = "") -> dict:
    """Gemini를 사용한 카페 일상 글 생성 (900~1100자)

    Args:
        user_instructions: 키워드 및 추가 요청사항
        category: 카테고리명

    Returns:
        dict: {"content": 생성된 글, "persona": 사용된 페르소나}
    """
    parsed = parse_query(user_instructions)
    keyword = parsed.get("keyword", "")
    note = parsed.get("note", "") or ""

    if not keyword:
        raise ValueError("키워드가 없습니다.")

    persona = get_random_persona()

    system = get_gemini_cafe_daily_system_prompt()
    user = get_gemini_cafe_daily_user_prompt(
        keyword=keyword,
        category=category,
        note=note,
        persona=persona,
    )

    text = call_ai(
        model_name=MODEL_NAME,
        system_prompt=system,
        user_prompt=user,
    )

    text = comprehensive_text_clean(text)

    return {"content": text, "persona": persona}
