"""Gemini 3 Pro - 원고 생성 서비스"""

from __future__ import annotations
import re
import time

from _prompts.service.get_mongo_prompt import get_mongo_prompt
from _prompts.grok.system import get_grok_system_prompt
from _prompts.common.ver1 import V1
from _constants.Model import Model
from utils.query_parser import parse_query
from utils.text_cleaner import comprehensive_text_clean
from utils.ai_client_factory import call_ai


MODEL_NAME: str = Model.GEMINI_3_PRO


def gemini_3_pro_gen(user_instructions: str, ref: str = "", category: str = "") -> str:
    """Gemini 3 Pro를 사용한 원고 생성"""

    parsed = parse_query(user_instructions)
    keyword = parsed.get("keyword", "")
    note = parsed.get("note", "") or ""

    if not keyword:
        raise ValueError("키워드가 없습니다.")

    mongo_data = get_mongo_prompt(category, user_instructions)

    system = get_grok_system_prompt(
        keyword=keyword,
        category=category,
    )

    user = f"""
키워드: {keyword}

추가 요청: {note}

참조 원고: {ref}

{V1}
""".strip()





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
