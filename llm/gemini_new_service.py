"""Gemini New - 범용 정보성 원고 생성 서비스 (Gemini 3 Flash Preview)"""

from __future__ import annotations
import re

from _prompts.gemini.new_system import get_gemini_new_system_prompt
from _prompts.gemini.new_user import get_gemini_new_user_prompt
from _constants.Model import Model
from utils.query_parser import parse_query
from utils.text_cleaner import comprehensive_text_clean
from utils.ai_client_factory import call_ai


MODEL_NAME: str = Model.GEMINI_3_FLASH_PREVIEW


def gemini_new_gen(user_instructions: str, ref: str = "", category: str = "") -> str:
    """Gemini 3 Flash Preview를 사용한 범용 정보성 원고 생성"""

    parsed = parse_query(user_instructions)
    keyword = parsed.get("keyword", "")
    note = parsed.get("note", "") or ""

    if not keyword:
        raise ValueError("키워드가 없습니다.")

    system = get_gemini_new_system_prompt()
    user = get_gemini_new_user_prompt(
        keyword=keyword,
        category=category,
        note=note,
        ref=ref,
    )





    text = call_ai(
        model_name=MODEL_NAME,
        system_prompt=system,
        user_prompt=user,
    )

    text = comprehensive_text_clean(text)

    length_no_space = len(re.sub(r"\s+", "", text))



    return text
