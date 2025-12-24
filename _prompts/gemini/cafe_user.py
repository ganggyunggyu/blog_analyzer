"""Gemini Cafe - 카페 짧은 글 유저 프롬프트"""


def get_gemini_cafe_user_prompt(
    keyword: str,
    category: str = "",
    note: str = "",
) -> str:
    """Gemini Cafe 유저 프롬프트 생성

    Args:
        keyword: 메인 키워드
        category: 카테고리
        note: 추가 요청사항

    Returns:
        구조화된 유저 프롬프트
    """

    prompt = f"""
## Input
- 키워드: {keyword}
- 카테고리: {category if category else "일반"}
- 추가 요청: {note if note else "없음"}

## Task
위 키워드에 대해 네이버 카페 짧은 글을 작성하세요.

## Requirements
1. 본문 250~300자 (공백 제외) - 반드시 지켜야 함
2. 짧고 캐주얼한 제목 (10~20자)
3. 소제목/번호 없이 자연스러운 흐름
4. 친근하고 일상적인 대화체
5. 핵심만 간단하게

## Output
제목 + 빈 줄 + 본문 형식으로 출력하세요.
"""

    return prompt.strip()
