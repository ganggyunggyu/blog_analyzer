"""Gemini New - 범용 정보성 원고 생성 서비스 (Gemini 3 Flash Preview)"""

from __future__ import annotations
import re

from _prompts.gemini.new_system import get_gemini_new_system_prompt
from _prompts.gemini.new_user import get_gemini_new_user_prompt
from _constants.Model import Model
from utils.query_parser import parse_query
from utils.text_cleaner import comprehensive_text_clean
from utils.ai_client_factory import call_ai
from utils.logger import log


MODEL_NAME: str = Model.GEMINI_3_PRO


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

    # 디버그: 프롬프트 길이 확인
    log.info(f"[DEBUG] 시스템 프롬프트 길이: {len(system)}자")
    log.info(f"[DEBUG] 유저 프롬프트 길이: {len(user)}자")

    try:
        text = call_ai(
            model_name=MODEL_NAME,
            system_prompt=system,
            user_prompt=user,
        )
    except Exception as e:
        log.error(f"[DEBUG] call_ai 에러: {type(e).__name__}: {e}")
        raise

    # 디버그: 응답 길이 확인
    log.info(f"[DEBUG] 응답 길이: {len(text)}자")
    if len(text) < 100:
        log.warning(f"[DEBUG] 짧은 응답: {text!r}")

    text = comprehensive_text_clean(text)

    return text
