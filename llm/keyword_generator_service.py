"""키워드-카테고리 매핑 생성 서비스 - Gemini Flash 기반"""

from __future__ import annotations

from _constants.Model import Model
from _prompts.keyword_generator import (
    get_keyword_generator_example_keywords,
    get_keyword_generator_system_prompt,
)
from utils.ai_client_factory import call_ai


MODEL_NAME: str = Model.GEMINI_3_FLASH_PREVIEW


def generate_keywords(
    categories: list[str],
    count: int = 60,
    include_keywords: list[str] | None = None,
    exclude_keywords: list[str] | None = None,
    shuffle: bool = True,
    note: str = "",
    prompt_profile: str = "default",
) -> dict:
    """카테고리별 키워드 매핑 생성"""
    if not categories:
        raise ValueError("카테고리 목록이 필요합니다.")

    example_keywords = _get_example_keyword_set()
    if not example_keywords:
        raise ValueError("예시 키워드 목록이 비어 있습니다.")

    system_prompt = get_keyword_generator_system_prompt(prompt_profile)

    # 유저 프롬프트 구성
    include_section = f"\n[포함 키워드]\n{', '.join(include_keywords)} (10~30% 빈도로 섞어서)" if include_keywords else ""
    exclude_section = f"\n[제외 키워드]\n{', '.join(exclude_keywords)}" if exclude_keywords else ""
    shuffle_section = "\n[배치 방식]\n뒤죽박죽 섞어서 (같은 카테고리 연속 최소화)" if shuffle else ""
    note_section = f"\n[추가 요청]\n{note}" if note else ""

    user_prompt = f"""[카테고리 목록]
{', '.join(categories)}

[생성 개수]
{count}개{include_section}{exclude_section}{shuffle_section}{note_section}"""

    raw_output = call_ai(
        model_name=MODEL_NAME,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
    )

    # 파싱: "키워드:카테고리" 형태만 추출
    keywords = _parse_output(raw_output, categories, example_keywords)

    return {
        "keywords": keywords,
        "raw": raw_output,
        "count": len(keywords),
        "model": MODEL_NAME,
    }


VALID_TYPES = {"일상", "자사키워드", "광고"}


def _get_example_keyword_set() -> set[str]:
    """예시 키워드 목록"""
    return {keyword for keyword in get_keyword_generator_example_keywords() if keyword}


def _parse_output(
    text: str,
    valid_categories: list[str],
    allowed_keywords: set[str],
) -> list[dict]:
    """출력 파싱: 키워드:카테고리:종류 형태 추출"""
    results = []
    seen_keywords = set()

    for line in text.strip().split("\n"):
        line = line.strip()
        if not line or ":" not in line:
            continue

        parts = line.split(":")
        if len(parts) < 2:
            continue

        keyword = parts[0].strip()
        category = parts[1].strip()
        keyword_type = parts[2].strip() if len(parts) >= 3 else "일상"

        if not keyword or not category:
            continue

        if category not in valid_categories:
            continue

        if keyword_type not in VALID_TYPES:
            keyword_type = "일상"

        if keyword not in allowed_keywords:
            continue

        if keyword in seen_keywords:
            continue

        seen_keywords.add(keyword)
        results.append(
            {
                "keyword": keyword,
                "category": category,
                "type": keyword_type,
            }
        )

    return results
