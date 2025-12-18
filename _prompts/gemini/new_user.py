"""Gemini New - 유저 프롬프트 템플릿 (Gemini 최적화)

Gemini 공식 권장:
- User content: 과업 + 입력 데이터
- 명확한 입력 구조
"""


def get_gemini_new_user_prompt(
    keyword: str,
    category: str = "",
    note: str = "",
    ref: str = "",
) -> str:
    """Gemini New 유저 프롬프트 생성

    Args:
        keyword: 메인 키워드
        category: 카테고리
        note: 추가 요청사항
        ref: 참조 문서

    Returns:
        구조화된 유저 프롬프트
    """

    prompt = f"""
## Input
- 키워드: {keyword}
- 카테고리: {category if category else "일반"}
- 추가 요청: {note if note else "없음"}
- 참조 문서: {ref if ref else "없음"}

## Task
위 키워드에 대해 정보성 블로그 원고를 작성하세요.

## Requirements
1. 독자가 궁금해할 정보를 풍성하게 담기
2. 직접 경험한 것처럼 생생하게 서술
3. 색다르고 독창적인 정보 위주
4. 정보량을 풍부하게 (구구절절한 설명보단 확실한 정보)
5. 연관 키워드도 자연스럽게 포함

## Output
제목과 본문만 출력하세요.
"""

    return prompt.strip()
