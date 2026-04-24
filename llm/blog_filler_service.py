"""Blog Filler - 블로그 글밥 쌓기 전용 서비스"""

from __future__ import annotations

from _prompts.blog_filler.system import get_blog_filler_system_prompt
from _prompts.blog_filler.user import get_blog_filler_user_prompt
from _constants.Model import Model
from llm.blog_filler_diet_v2_service import (
    KEYWORD_FAMILY_MAP as DIET_V2_KEYWORD_FAMILY_MAP,
    blog_filler_diet_v2_gen,
)
from services.naver_blog_reference_service import collect_naver_view_titles
from utils.query_parser import parse_query
from utils.text_cleaner import comprehensive_text_clean, remove_markdown
from utils.ai_client_factory import call_ai
from utils.logger import log


MODEL_NAME: str = Model.CLAUDE_SONNET_4_6
NAVER_TITLE_EXAMPLE_LIMIT = 8
DIET_V2_BLOG_FILLER_CATEGORIES: set[str] = {
    "다이어트",
    "다이어트보조제",
    "브로멜라인",
}


def should_use_diet_v2_blog_filler(keyword: str, category: str) -> bool:
    normalized_keyword = (keyword or "").strip()
    normalized_category = (category or "").strip()

    if normalized_keyword in DIET_V2_KEYWORD_FAMILY_MAP:
        return True

    return normalized_category in DIET_V2_BLOG_FILLER_CATEGORIES


def get_naver_title_examples(keyword: str) -> list[str]:
    try:
        titles = collect_naver_view_titles(
            keyword,
            limit=NAVER_TITLE_EXAMPLE_LIMIT,
        )
    except Exception as exc:
        log.warning(
            "네이버 검색 제목 수집 실패",
            keyword=keyword,
            error=str(exc),
        )
        return []

    if titles:
        log.info("네이버 검색 제목 수집 완료", keyword=keyword, count=len(titles))
    return titles


def blog_filler_gen(user_instructions: str, ref: str = "", category: str = "") -> str:
    """블로그 글밥 생성"""

    parsed = parse_query(user_instructions)
    keyword = parsed.get("keyword", "")
    note = parsed.get("note", "") or ""

    if not keyword:
        raise ValueError("키워드가 없습니다.")

    naver_title_examples = get_naver_title_examples(keyword)

    if should_use_diet_v2_blog_filler(keyword=keyword, category=category):
        log.info(f"diet_v2_blog_filler 라우팅 keyword={keyword} category={category}")
        result = blog_filler_diet_v2_gen(
            user_instructions=user_instructions,
            live_view_titles=naver_title_examples,
            category=category or "다이어트",
        )
        return str(result["manuscript"])

    system = get_blog_filler_system_prompt(category=category, keyword=keyword)
    user = get_blog_filler_user_prompt(
        keyword=keyword,
        category=category,
        note=note,
        ref=ref,
        naver_title_examples=naver_title_examples,
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
