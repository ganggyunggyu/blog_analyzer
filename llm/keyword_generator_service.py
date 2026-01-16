"""키워드-카테고리 매핑 생성 서비스 - Gemini Flash 기반"""

from __future__ import annotations

from _constants.Model import Model
from _prompts.keyword_generator import get_keyword_generator_system_prompt
from utils.ai_client_factory import call_ai


MODEL_NAME: str = Model.GROK_4_NON_RES


def generate_keywords(
    categories: list[str],
    count: int = 60,
    include_keywords: list[str] | None = None,
    exclude_keywords: list[str] | None = None,
    shuffle: bool = True,
    note: str = "",
) -> dict:
    """키워드-카테고리 매핑 생성

    Args:
        categories: 사용 가능한 카테고리 목록 (필수)
        count: 생성할 키워드 개수 (기본 60)
        include_keywords: 포함해야 할 키워드 목록 (선택)
        exclude_keywords: 제외해야 할 키워드 목록 (선택)
        shuffle: 카테고리 뒤죽박죽 섞기 (기본 True)
        note: 추가 요청사항 (선택)

    Returns:
        dict: {
            "keywords": 생성된 키워드:카테고리 리스트,
            "raw": 원본 텍스트,
            "count": 생성된 개수,
            "model": 사용된 모델
        }
    """
    if not categories:
        raise ValueError("카테고리 목록이 필요합니다.")

    system_prompt = get_keyword_generator_system_prompt()

    # 유저 프롬프트 구성
    user_parts = [f"[카테고리 목록]\n{', '.join(categories)}"]
    user_parts.append(f"\n[생성 개수]\n{count}개")

    if include_keywords:
        user_parts.append(
            f"\n[포함 키워드]\n{', '.join(include_keywords)} (10~30% 빈도로 섞어서)"
        )

    if exclude_keywords:
        user_parts.append(f"\n[제외 키워드]\n{', '.join(exclude_keywords)}")

    if shuffle:
        user_parts.append("\n[배치 방식]\n뒤죽박죽 섞어서 (같은 카테고리 연속 최소화)")

    if note:
        user_parts.append(f"\n[추가 요청]\n{note}")

    user_prompt = "\n".join(user_parts)

    raw_output = call_ai(
        model_name=MODEL_NAME,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
    )

    # 파싱: "키워드:카테고리" 형태만 추출
    keywords = _parse_output(raw_output, categories)

    return {
        "keywords": keywords,
        "raw": raw_output,
        "count": len(keywords),
        "model": MODEL_NAME,
    }


def _parse_output(text: str, valid_categories: list[str]) -> list[dict]:
    """출력 파싱: 키워드:카테고리 형태 추출"""
    results = []
    seen_keywords = set()

    for line in text.strip().split("\n"):
        line = line.strip()
        if not line or ":" not in line:
            continue

        # 콜론으로 분리 (첫 번째 콜론 기준)
        parts = line.split(":", 1)
        if len(parts) != 2:
            continue

        keyword = parts[0].strip()
        category = parts[1].strip()

        # 유효성 검사
        if not keyword or not category:
            continue

        # 카테고리 유효성 검사
        if category not in valid_categories:
            continue

        # 중복 키워드 제거
        if keyword in seen_keywords:
            continue

        seen_keywords.add(keyword)
        results.append(
            {
                "keyword": keyword,
                "category": category,
            }
        )

    return results
