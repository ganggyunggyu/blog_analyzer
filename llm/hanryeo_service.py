"""한려담원 - 블로그 원고 생성 서비스"""

from __future__ import annotations

from _prompts.hanryeo.system import get_hanryeo_system_prompt
from _prompts.hanryeo.system_en import get_hanryeo_system_prompt_en
from _prompts.hanryeo.user import get_hanryeo_user_prompt
from _prompts.hanryeo.user_en import get_hanryeo_user_prompt_en
from _constants.Model import Model
from utils.query_parser import parse_query
from utils.text_cleaner import comprehensive_text_clean, remove_markdown
from utils.ai_client_factory import call_ai
from utils.logger import log


MODEL_NAME: str = Model.GPT5_4_MINI
TEMPERATURE: float = 0.85

# ── 프롬프트 언어 설정 ──────────────────────────────
# "ko" = 기존 한국어 프롬프트
# "en" = 영어 프롬프트 (Anthropic 가이드 구조, 비용 절약)
PROMPT_LANG: str = "ko"
# ───────────────────────────────────────────────────

PROMPT_BUILDERS = {
    "ko": {
        "system": get_hanryeo_system_prompt,
        "user": get_hanryeo_user_prompt,
    },
    "en": {
        "system": get_hanryeo_system_prompt_en,
        "user": get_hanryeo_user_prompt_en,
    },
}


def hanryeo_gen(
    user_instructions: str,
    ref: str = "",
    category: str = "",
) -> str:
    """한려담원 원고 생성"""

    parsed = parse_query(user_instructions)
    keyword = parsed.get("keyword", "")
    note = parsed.get("note", "") or ""

    if not keyword:
        raise ValueError("키워드가 없습니다.")

    builders = PROMPT_BUILDERS.get(PROMPT_LANG, PROMPT_BUILDERS["ko"])
    system = builders["system"]()
    user = builders["user"](
        keyword=keyword,
        category=category,
        note=note,
        ref=ref,
    )

    log.info(f"[{PROMPT_LANG}] 프롬프트 sys={len(system)} user={len(user)}")

    try:
        text = call_ai(
            model_name=MODEL_NAME,
            system_prompt=system,
            user_prompt=user,
            temperature=TEMPERATURE,
        )
    except Exception as e:
        log.error(f"call_ai 에러: {e}")
        raise

    log.info(
        f"응답 len={len(text)}" + (f" | {text[:50]!r}..." if len(text) < 100 else "")
    )

    text = comprehensive_text_clean(text)

    return text
