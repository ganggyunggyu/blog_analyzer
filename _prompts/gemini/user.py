"""Gemini 유저 프롬프트 템플릿"""


def get_gemini_user_prompt(keyword: str, note: str, ref: str) -> str:
    """Gemini 유저 프롬프트 생성"""
    return f"""
    '{keyword}'에 대한 네이버 블로그 글을 작성해주세요.

    추가 요청: {note} 3000단어 이상
    추가 요청은 어떤일이 있어도 최우선으로 지켜져야 합니다.

    참조 원고: {ref}
    """.strip()
