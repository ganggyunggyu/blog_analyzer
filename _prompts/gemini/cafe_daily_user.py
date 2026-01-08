"""Gemini Cafe Daily - 카페 일상 글 유저 프롬프트"""


def get_gemini_cafe_daily_user_prompt(
    keyword: str,
    category: str = "",
    note: str = "",
    persona: str = "",
) -> str:
    """Gemini Cafe Daily 유저 프롬프트 생성

    Args:
        keyword: 메인 키워드
        category: 카테고리
        note: 추가 요청사항
        persona: 화자 페르소나

    Returns:
        구조화된 유저 프롬프트
    """

    prompt = f"""
## Input
- 키워드: {keyword}
- 카테고리: {category if category else "일반"}
- 화자: {persona if persona else "일반"}
- 추가 요청: {note if note else "없음"}

## Task
위 키워드에 대해 네이버 카페 일상 글을 작성하세요.
화자의 성격과 말투를 반영해서 글을 써주세요.

## Requirements
1. 본문 900~1100자 (공백 제외) - 반드시 지켜야 함
2. 일상적이고 자연스러운 제목 (15~25자)
3. 소제목/번호 없이 자연스러운 일상 흐름
4. 오늘의 일기, 경험담 느낌으로
5. 3~4개 문단, 자연스러운 이야기 전개
6. 화자 성격에 맞는 말투 사용

## Output
제목 + 빈 줄 + 본문 형식으로 출력하세요.
"""

    return prompt.strip()
