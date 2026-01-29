"""Blog Filler - 블로그 글밥 쌓기 전용 서비스"""

from __future__ import annotations

from _prompts.blog_filler.system import get_blog_filler_system_prompt
from _prompts.blog_filler.user import get_blog_filler_user_prompt
from _constants.Model import Model
from utils.query_parser import parse_query
from utils.text_cleaner import comprehensive_text_clean, remove_markdown
from utils.ai_client_factory import call_ai
from utils.logger import log


MODEL_NAME: str = Model.GROK_4_NON_RES


def blog_filler_gen(user_instructions: str, ref: str = "", category: str = "") -> str:
    """블로그 글밥 생성"""

    parsed = parse_query(user_instructions)
    keyword = parsed.get("keyword", "")
    note = parsed.get("note", "") or ""

    if not keyword:
        raise ValueError("키워드가 없습니다.")

    system = get_blog_filler_system_prompt()
    user = get_blog_filler_user_prompt(
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

    text = remove_markdown(text)
    text = comprehensive_text_clean(text)

    return text
