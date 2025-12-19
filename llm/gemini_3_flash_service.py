"""Gemini 3 Flash Preview - 원고 생성 서비스"""

from __future__ import annotations
import re
import time

from _prompts.gemini.flash_system import get_gemini_flash_system_prompt
from _prompts.gemini.flash_user import get_gemini_flash_user_prompt
from _constants.Model import Model
from utils.query_parser import parse_query
from utils.text_cleaner import comprehensive_text_clean
from utils.ai_client_factory import call_ai


MODEL_NAME: str = Model.GEMINI_3_FLASH_PREVIEW


def gemini_3_flash_gen(user_instructions: str, ref: str = "", category: str = "") -> str:
    """Gemini 3 Flash Preview를 사용한 원고 생성"""

    parsed = parse_query(user_instructions)
    keyword = parsed.get("keyword", "")
    note = parsed.get("note", "") or ""

    if not keyword:
        raise ValueError("키워드가 없습니다.")

    system = get_gemini_flash_system_prompt(keyword=keyword, category=category)
    user = get_gemini_flash_user_prompt(keyword=keyword, note=note, ref=ref)





    start_ts = time.time()

    text = call_ai(
        model_name=MODEL_NAME,
        system_prompt=system,
        user_prompt=user,
    )

    text = comprehensive_text_clean(text)

    length_no_space = len(re.sub(r"\s+", "", text))
    elapsed = time.time() - start_ts





    return text
