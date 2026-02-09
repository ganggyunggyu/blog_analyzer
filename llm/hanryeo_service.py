"""한려담원 - 블로그 원고 생성 서비스"""

from __future__ import annotations

from _prompts.hanryeo.system import get_hanryeo_system_prompt
from _prompts.hanryeo.user import get_hanryeo_user_prompt
from _constants.Model import Model
from utils.query_parser import parse_query
from utils.text_cleaner import comprehensive_text_clean, remove_markdown
from utils.ai_client_factory import call_ai
from utils.logger import log


MODEL_NAME: str = Model.GROK_4_1_RES


def hanryeo_gen(user_instructions: str, ref: str = "", category: str = "") -> str:
    """한려담원 원고 생성"""

    parsed = parse_query(user_instructions)
    keyword = parsed.get("keyword", "")
    note = parsed.get("note", "") or ""

    if not keyword:
        raise ValueError("키워드가 없습니다.")

    system = get_hanryeo_system_prompt()
    user = get_hanryeo_user_prompt(
        keyword=keyword,
        category=category,
        note=note,
        ref=ref,
    )

    log.info(f"프롬프트 sys={len(system)} user={len(user)}")

    try:
        text = call_ai(
            model_name=MODEL_NAME,
            system_prompt=system,
            user_prompt=user,
        )
    except Exception as e:
        log.error(f"call_ai 에러: {e}")
        raise

    log.info(
        f"응답 len={len(text)}" + (f" | {text[:50]!r}..." if len(text) < 100 else "")
    )

    # ✔ 보존 (remove_markdown이 체크 이모지를 제거하므로 임시 치환)
    # _CHECK = "%%CHECK%%"
    # text = text.replace("✔", _CHECK)
    # text = remove_markdown(text)
    text = comprehensive_text_clean(text)
    # text = text.replace(_CHECK, "✔")

    return text
