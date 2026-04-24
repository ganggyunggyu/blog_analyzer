"""한려담원 - 블로그 원고 생성 서비스"""

from __future__ import annotations

import re

from _prompts.hanryeo.system import get_hanryeo_system_prompt
from _prompts.hanryeo.system_en import get_hanryeo_system_prompt_en
from _prompts.hanryeo.user import get_hanryeo_user_prompt
from _prompts.hanryeo.user_en import get_hanryeo_user_prompt_en
from _constants.Model import Model
from llm.hanryeo_output_cleanup import sanitize_hanryeo_output
from services.naver_blog_reference_service import build_naver_blog_reference_bundle
from utils.query_parser import parse_query
from utils.text_cleaner import comprehensive_text_clean
from utils.ai_client_factory import call_ai
from utils.logger import log


MODEL_NAME: str = Model.DEEPSEEK_V4_FLASH
TEMPERATURE: float = 0.85
MAX_GENERATION_ATTEMPTS: int = 2

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


def _extract_numbered_headings(text: str) -> list[str]:
    return [
        line.strip()
        for line in text.splitlines()
        if re.match(r"^\d+\.\s+\S", line.strip())
    ]


def _validate_hanryeo_structure(text: str) -> list[str]:
    headings = _extract_numbered_headings(text)
    numbers = [
        int(match.group(1))
        for heading in headings
        if (match := re.match(r"^(\d+)\.\s+", heading))
    ]
    issues: list[str] = []

    if numbers != [1, 2, 3, 4, 5]:
        issues.append(
            "번호 소제목은 정확히 1~5까지 한 번씩만 필요합니다. "
            f"현재 번호={numbers}"
        )

    for heading in headings:
        if re.search(r"(마무리|결론|제품\s*연결|정리)", heading) and not heading.startswith("5."):
            issues.append(f"마무리 역할이 5번이 아닌 소제목에 들어갔습니다: {heading}")

    return issues


def _merge_retry_note(note: str, issues: list[str]) -> str:
    issue_text = "\n".join(f"- {issue}" for issue in issues)
    retry_note = f"""[재작성 강제 조건]
이전 출력은 한려담원 구조 검수에서 실패했습니다.
아래 문제를 반드시 고쳐서 다시 작성하세요.
{issue_text}

필수 출력 구조:
1. 첫 번째 소제목
2. 두 번째 소제목
3. 세 번째 소제목
4. 실천/주의/Q&A 소제목
5. 결론/제품 연결 소제목

본문 안에서는 숫자 번호 목록을 쓰지 말고 ✔ 기호만 사용하세요.
4번에서 글을 끝내지 말고 반드시 5번 소제목과 본문까지 작성하세요."""

    if note.strip():
        return f"{note.strip()}\n\n{retry_note}"
    return retry_note


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
    reference_bundle = build_naver_blog_reference_bundle(
        query=keyword,
        manual_ref=ref,
    )
    issues: list[str] = []
    text = ""

    for attempt in range(1, MAX_GENERATION_ATTEMPTS + 1):
        attempt_note = _merge_retry_note(note=note, issues=issues) if issues else note
        user = builders["user"](
            keyword=keyword,
            category=category,
            note=attempt_note,
            ref=reference_bundle,
        )

        log.info(f"[{PROMPT_LANG}] 프롬프트 sys={len(system)} user={len(user)} attempt={attempt}")

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
        text = sanitize_hanryeo_output(text)
        issues = _validate_hanryeo_structure(text)
        if not issues:
            return text

        log.warning(f"한려담원 구조 검수 실패 attempt={attempt} issues={issues}")

    return text
