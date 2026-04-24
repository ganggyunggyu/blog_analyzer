"""Blog Filler - 유저 프롬프트 템플릿"""


def get_blog_filler_user_prompt(
    keyword: str,
    category: str = "",
    note: str = "",
    ref: str = "",
    naver_title_examples: list[str] | None = None,
) -> str:
    """Blog Filler 유저 프롬프트 생성

    Args:
        keyword: 메인 키워드
        category: 카테고리
        note: 추가 요청사항
        ref: 참조 문서
        naver_title_examples: 네이버 검색 결과 제목 예시

    Returns:
        구조화된 유저 프롬프트
    """

    parts = [f"## Input\n- 키워드: {keyword}"]

    if category:
        parts.append(f"- 카테고리: {category}")

    parts.append("\n키워드 기반의 블로그 원고를 작성해 주세요.")
    parts.append("반드시 키워드와 카테고리에 맞는 주제로 작성하세요.")

    if note:
        parts.append(f"\n## 추가 요청사항\n{note}")

    title_examples = [
        title.strip()
        for title in naver_title_examples or []
        if title and title.strip()
    ]
    if title_examples:
        parts.append("\n## 네이버 검색 제목 예시")
        parts.append("아래 제목은 현재 네이버 검색 결과에서 보이는 블로그 제목입니다.")
        parts.append("검색 의도와 제목 리듬만 참고하고 문장을 그대로 베끼지 마세요.")
        parts.append("예시 제목과 완전히 같은 제목은 만들지 마세요.")
        parts.extend(f"- {title}" for title in title_examples[:8])

    if ref:
        parts.append(f"\n## 참조 문서\n{ref}")

    parts.append("\n## Output\n제목과 본문만 출력하세요.")

    prompt = "\n".join(parts)

    return prompt.strip()
