"""Restaurant(맛집) 유저 프롬프트 템플릿"""

from _prompts.rules.line_break_rules import line_break_rules


def get_restaurant_user_prompt() -> str:
    """Restaurant(맛집) 유저 프롬프트 생성"""
    return f"""
지침 기반 원고작성 시작

- 일본어 금지 영어 병신같은 표현 금지 한자 금지

# 줄바꿈 지침
{line_break_rules}
""".strip()
