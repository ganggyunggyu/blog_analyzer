"""Gemini Cafe Daily - 카페 일상 글 생성 서비스 (900~1100자)"""

from __future__ import annotations
import random

from _prompts.comment import PERSONAS, get_persona_by_id
from _prompts.viral import get_post_system_prompt, get_post_user_prompt
from _constants.Model import Model
from utils.query_parser import parse_query
from utils.text_cleaner import comprehensive_text_clean
from utils.ai_client_factory import call_ai


MODEL_NAME: str = Model.GEMINI_3_FLASH_PREVIEW


# ============================================================
# 기존 프롬프트 import (주석처리)
# ============================================================
# from _prompts.gemini.cafe_daily_system import get_gemini_cafe_daily_system_prompt
# from _prompts.gemini.cafe_daily_user import get_gemini_cafe_daily_user_prompt
# ============================================================


def gemini_cafe_daily_gen(
    user_instructions: str,
    category: str = "",
    persona_id: str | None = None,
    persona_index: int | None = None,
    keyword_type: str = "자사",
    product_name: str = "한려담원 흑염소진액",
    viral_persona_id: int | None = None,
) -> dict:
    """Gemini를 사용한 카페 일상 글 생성 (900~1100자)"""
    parsed = parse_query(user_instructions)
    keyword = parsed.get("keyword", "")
    note = parsed.get("note", "") or ""

    if not keyword:
        raise ValueError("키워드가 없습니다.")

    # 페르소나 선택 (기존 PERSONAS 사용)
    if persona_id:
        used_id = persona_id
        persona = get_persona_by_id(persona_id)
    elif persona_index is not None:
        used_id, persona, _ = PERSONAS[persona_index]
    else:
        weights = [w for _, _, w in PERSONAS]
        used_id, persona, _ = random.choices(PERSONAS, weights=weights, k=1)[0]

    # 새 바이럴 프롬프트 사용
    system = get_post_system_prompt()
    user = get_post_user_prompt(
        keyword=keyword,
        keyword_type=keyword_type,
        product_name=product_name,
        persona_id=viral_persona_id or random.randint(1, 15),
    )

    # ============================================================
    # 기존 프롬프트 (주석처리)
    # ============================================================
    # system = get_gemini_cafe_daily_system_prompt()
    # user = get_gemini_cafe_daily_user_prompt(
    #     keyword=keyword,
    #     category=category,
    #     note=note,
    #     persona=persona,
    # )
    # ============================================================

    from utils.logger import log

    log.info(f"[DEBUG] keyword={keyword!r}, persona={persona!r}")
    log.info(f"[DEBUG] user_prompt 길이={len(user)}")

    text = call_ai(
        model_name=MODEL_NAME,
        system_prompt=system,
        user_prompt=user,
    )

    log.info(f"[DEBUG] 응답 원문: {text[:200]!r}..." if len(text) > 200 else f"[DEBUG] 응답 원문: {text!r}")

    text = comprehensive_text_clean(text)

    return {"content": text, "persona_id": used_id, "persona": persona}
