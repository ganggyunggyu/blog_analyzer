"""Blog Filler - 유저 프롬프트 템플릿"""


def get_blog_filler_user_prompt(
    keyword: str,
    category: str = "",
    note: str = "",
    ref: str = "",
) -> str:
    """Blog Filler 유저 프롬프트 생성

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

키워드 기반의 블로그 원고를 작성해 주세요.

## Output
제목과 본문만 출력하세요.
```
어쩌고저쩌고
```
"""

    return prompt.strip()
