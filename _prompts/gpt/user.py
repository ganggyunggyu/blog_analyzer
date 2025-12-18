"""GPT 유저 프롬프트 템플릿"""

from _prompts.rules import line_break_rules


def get_gpt_user_prompt(keyword: str, note: str, ref: str) -> str:
    """GPT 유저 프롬프트 생성"""
    return f"""
    키워드: {keyword}

    추가 요청: {note}

    참조 원고: {ref}

{line_break_rules}
    """.strip()
