"""Gemini Cafe Daily - 카페 일상 글 유저 프롬프트"""


def get_gemini_cafe_daily_user_prompt(
    keyword: str,
    category: str = "",
    note: str = "",
    persona: str = "",
) -> str:
    """Gemini Cafe Daily 유저 프롬프트 생성"""

    prompt = f"""
<input>
<keyword>{keyword}</keyword>
<category>{category if category else "일반"}</category>
<persona>{persona if persona else "일반"}</persona>
<note>{note if note else "없음"}</note>
</input>

<task>
위 키워드로 네이버 카페 일상 글 작성.
화자의 성격과 말투 반영.
정확한 정보 포함 (가격/효과/기간 중 2개 이상).
500-700자.
</task>
"""

    return prompt.strip()
