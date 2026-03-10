"""키워드-카테고리 매핑 생성 서비스 - Gemini Flash 기반"""

from __future__ import annotations

from _constants.Model import Model
from _prompts.keyword_generator import (
    get_keyword_generator_system_prompt,
)
from utils.ai_client_factory import call_ai


MODEL_NAME: str = Model.GROK_4_1_NON_RES


def _build_section(title: str, content: str) -> str:
    if not content:
        return ""
    return f"""
[{title}]
{content}"""


def _parse_keyword_lines(raw: str) -> list[dict]:
    """AI 응답을 파싱하여 keyword/category/type dict 리스트로 변환"""
    results: list[dict] = []
    for line in raw.strip().splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split(":")
        if len(parts) >= 3:
            results.append({
                "keyword": parts[0].strip(),
                "category": parts[1].strip(),
                "type": parts[2].strip(),
            })
        elif len(parts) == 2:
            results.append({
                "keyword": parts[0].strip(),
                "category": parts[1].strip(),
                "type": "일상",
            })
    return results


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

    system_prompt = get_keyword_generator_system_prompt(prompt_profile)

    shuffle_content = "뒤죽박죽 섞어서 (같은 카테고리 연속 최소화)" if shuffle else ""

    user_prompt = f"""[카테고리 목록]
{', '.join(categories)}

[생성 개수]
{count}개{_build_section("배치 방식", shuffle_content)}{_build_section("추가 요청", note)}"""

    raw_output = call_ai(
        model_name=MODEL_NAME,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
    )

    keywords = _parse_keyword_lines(raw_output)

    return {
        "keywords": keywords,
        "raw": raw_output,
        "count": len(keywords),
        "model": MODEL_NAME,
    }
