"""알리바바 - 단일 스타일 블로그 원고 생성 서비스"""

from __future__ import annotations

import re

from _constants.Model import Model
from _prompts.alibaba.profile import resolve_alibaba_profile
from _prompts.alibaba.system import get_alibaba_system_prompt
from _prompts.alibaba.user import get_alibaba_user_prompt
from services.naver_blog_reference_service import collect_naver_blog_references
from utils.ai_client_factory import call_ai
from utils.logger import log
from utils.query_parser import parse_query
from utils.text_cleaner import comprehensive_text_clean, remove_markdown


MODEL_NAME: str = Model.GEMINI_3_FLASH_PREVIEW
AUTO_REFERENCE_LIMIT = 8
REFERENCE_BODY_CHAR_LIMIT = 3500
ALIBABA_DOT_COM_PATTERN = re.compile(
    r"(?<![A-Za-z0-9])(?:Alibaba|alibaba)\.com(?![A-Za-z0-9])"
)
ALIBABA_DOT_COM_WITH_KOREAN_PATTERN = re.compile(
    r"알리바바(?:닷컴)?\s*\(\s*(?:Alibaba|alibaba)\.com\s*\)"
)
SIXTEEN_EIGHT_DOT_COM_PATTERN = re.compile(
    r"(?<![A-Za-z0-9])1688\.com(?![A-Za-z0-9])",
    re.I,
)


def _trim_reference_body(body: str) -> str:
    cleaned = body.strip()
    if len(cleaned) <= REFERENCE_BODY_CHAR_LIMIT:
        return cleaned
    return cleaned[:REFERENCE_BODY_CHAR_LIMIT].rstrip()


def build_alibaba_reference_bundle(
    keyword: str,
    manual_ref: str = "",
) -> tuple[str, int]:
    try:
        references = collect_naver_blog_references(
            keyword,
            limit=AUTO_REFERENCE_LIMIT,
        )
    except Exception as exc:
        log.warning(
            "알리바바 네이버 참조원고 수집 실패",
            keyword=keyword,
            error=str(exc),
        )
        references = []

    parts: list[str] = []

    if references:
        auto_ref_parts = [
            "[자동 수집 참고원고]",
            "아래 원고들은 같은 키워드로 노출된 네이버 블로그 글입니다.",
            "문장을 그대로 베끼지 말고 정보, 검색 의도, 약점만 분석하세요.",
        ]

        for index, reference in enumerate(references, start=1):
            auto_ref_parts.append(
                "\n".join(
                    [
                        f"[참조 {index}]",
                        f"제목: {reference.title}",
                        "본문:",
                        _trim_reference_body(reference.body),
                    ]
                )
            )

        parts.append("\n\n".join(auto_ref_parts).strip())
        log.info(
            "알리바바 네이버 참조원고 수집 완료",
            keyword=keyword,
            reference_count=len(references),
        )

    cleaned_manual_ref = manual_ref.strip()
    if cleaned_manual_ref:
        parts.append(
            "\n\n".join(
                [
                    "[사용자 제공 참조원고]",
                    cleaned_manual_ref,
                ]
            )
        )

    return "\n\n".join(parts).strip(), len(references)


def sanitize_alibaba_output(text: str) -> str:
    text = remove_markdown(text)
    text = ALIBABA_DOT_COM_WITH_KOREAN_PATTERN.sub("알리바바닷컴", text)
    text = ALIBABA_DOT_COM_PATTERN.sub("알리바바닷컴", text)
    text = SIXTEEN_EIGHT_DOT_COM_PATTERN.sub("1688닷컴", text)
    text = text.replace("알리바바닷컴는", "알리바바닷컴은")
    text = text.replace("알리바바닷컴와", "알리바바닷컴과")
    text = text.replace("1688닷컴는", "1688닷컴은")
    text = text.replace("1688닷컴와", "1688닷컴과")
    return comprehensive_text_clean(text)


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
    reference_bundle, auto_reference_count = build_alibaba_reference_bundle(
        keyword=keyword,
        manual_ref=ref,
    )
    user = get_alibaba_user_prompt(
        keyword=keyword,
        note=note,
        ref=reference_bundle,
        category=category,
        profile=profile,
        auto_reference_count=auto_reference_count,
    )

    log.info(
        f"alibaba_gen | keyword={keyword} | category={category} | profile={profile.profile_id}"
    )

    text = call_ai(
        model_name=MODEL_NAME,
        system_prompt=system,
        user_prompt=user,
    )
    text = sanitize_alibaba_output(text)

    return {
        "content": text,
        "profile_id": profile.profile_id,
        "profile_label": profile.label,
    }
