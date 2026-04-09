"""알리바바 - 단일 스타일 블로그 원고 생성 서비스"""

from __future__ import annotations

from _constants.Model import Model
from _prompts.alibaba.profile import resolve_alibaba_profile
from _prompts.alibaba.system import get_alibaba_system_prompt
from _prompts.alibaba.user import get_alibaba_user_prompt
from utils.ai_client_factory import call_ai
from utils.logger import log
from utils.query_parser import parse_query
from utils.text_cleaner import comprehensive_text_clean


MODEL_NAME: str = Model.GEMINI_3_FLASH_PREVIEW


def alibaba_gen(
    user_instructions: str,
    ref: str = "",
    category: str = "",
) -> dict[str, str]:
    parsed = parse_query(user_instructions)
    keyword = parsed.get("keyword", "")
    note = parsed.get("note", "") or ""

    if not keyword:
        raise ValueError("키워드가 없습니다.")

    profile = resolve_alibaba_profile()
    system = get_alibaba_system_prompt(
        keyword=keyword,
        category=category,
        profile=profile,
    )
    user = get_alibaba_user_prompt(
        keyword=keyword,
        note=note,
        ref=ref,
        category=category,
        profile=profile,
    )

    log.info(
        f"alibaba_gen | keyword={keyword} | category={category} | profile={profile.profile_id}"
    )

    text = call_ai(
        model_name=MODEL_NAME,
        system_prompt=system,
        user_prompt=user,
    )
    text = comprehensive_text_clean(text)

    return {
        "content": text,
        "profile_id": profile.profile_id,
        "profile_label": profile.label,
    }
