"""Gemini Cafe Daily - 카페 일상 글 생성 서비스 (18종 페르소나)"""

from __future__ import annotations
import random

from _prompts.viral import get_post_system_prompt, get_post_user_prompt, PERSONAS, get_persona
from _constants.Model import Model
from utils.query_parser import parse_query
from utils.text_cleaner import comprehensive_text_clean
from utils.ai_client_factory import call_ai
from utils.logger import log


MODEL_NAME: str = Model.GEMINI_3_FLASH_PREVIEW


def gemini_cafe_daily_gen(
    user_instructions: str,
    category: str = "",
    persona_id: int | None = None,
    product_name: str = "한려담원 흑염소진액",
) -> dict:
    """Gemini를 사용한 카페 일상 글 생성 (18종 페르소나)"""
    parsed = parse_query(user_instructions)
    keyword = parsed.get("keyword", "")

    if not keyword:
        raise ValueError("키워드가 없습니다.")

    # 페르소나 선택 (1~18 랜덤 또는 지정)
    if persona_id and persona_id in PERSONAS:
        used_id = persona_id
    else:
        used_id = random.randint(1, 18)

    persona = get_persona(used_id)

    # 새 바이럴 프롬프트 사용
    system = get_post_system_prompt()
    user = get_post_user_prompt(
        keyword=keyword,
        product_name=product_name,
        persona_id=used_id,
    )

    log.info(f"[DEBUG] keyword={keyword!r}, persona={persona['name']!r}")
    log.info(f"[DEBUG] user_prompt 길이={len(user)}")

    text = call_ai(
        model_name=MODEL_NAME,
        system_prompt=system,
        user_prompt=user,
    )

    log.info(f"[DEBUG] 응답 원문: {text[:200]!r}..." if len(text) > 200 else f"[DEBUG] 응답 원문: {text!r}")

    text = comprehensive_text_clean(text)

    return {"content": text, "persona_id": used_id, "persona": persona["name"]}
