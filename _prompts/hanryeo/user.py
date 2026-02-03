"""한려담원 - 유저 프롬프트 템플릿"""


def get_hanryeo_user_prompt(
    keyword: str,
    category: str = "",
    note: str = "",
    ref: str = "",
) -> str:
    """한려담원 유저 프롬프트 생성"""

    parts = [f"## Input\n- 키워드: {keyword}"]

    if category:
        parts.append(f"- 카테고리: {category}")

    parts.append("\n키워드 기반의 블로그 원고를 작성해 주세요.")
    parts.append("반드시 키워드와 카테고리에 맞는 주제로 작성하세요.")

    if note:
        parts.append(f"\n## 추가 요청사항\n{note}")

    if ref:
        parts.append(f"\n## 참조 문서\n{ref}")

    parts.append("\n## Output\n제목과 본문만 출력하세요.")

    prompt = "\n".join(parts)

    return prompt.strip()
