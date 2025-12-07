"""Claude 유저 프롬프트 템플릿"""


def get_claude_user_prompt(keyword: str, note: str, ref: str) -> str:
    """Claude 유저 프롬프트 생성"""
    return f"""
## 원고 길이 지침

**필수 준수사항: 한글 기준 공백 제외 2,000단어 이상 작성**

### 섹션별 분량 가이드
- 서론 + 1~2번 소제목: 약 500딘어
- 3~4번 소제목: 1,200단어 이상
- 5번 소제목: 500단어 이상

    키워드: {keyword}

    추가 요청: {note}

    참조 원고: {ref}
    """.strip()
