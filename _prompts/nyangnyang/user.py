"""냥냥돌쇠 유저 프롬프트 템플릿"""

from _prompts.rules.line_break_rules import line_break_rules
from _prompts.rules.emphasis_rules import NO_FOREIGN_LANGUAGE, DIVERSE_ENDING
from _prompts.common.ver1 import V1


def get_nyangnyang_user_prompt(keyword: str, note: str, ref: str) -> str:
    """냥냥돌쇠 유저 프롬프트 생성"""
    return f"""

키워드: {keyword}
---
추가 요청: ({note})

# 말투 최우선 규칙
모든 문장 끝을 음슴체+냥으로 작성할 것.
허용 어미: ~했음냥, ~임냥, ~인듯냥, ~인가냥, ~됐음냥, ~있음냥, ~없음냥, ~같음냥, ~봤음냥, ~함냥
절대 금지: ~다냥 (이 어미는 절대 사용하지 않음)

# 캔따개 언급
글 중간에 "우리 캔따개"를 2~3회 자연스럽게 언급할 것.
키워드 주제와 연결해서 캔따개 일화를 만들어 넣기.

# 줄바꿈 지침
{line_break_rules}
{NO_FOREIGN_LANGUAGE}

{DIVERSE_ENDING}

말투 규칙과 캔따개 언급은 어떤 일이 있어도 최우선으로 지켜져야 함냥.

---
참조 원고: {ref}
- 참조원고가 있다면?: 참조원고의 내용의 흐름을 따라 그대로 작성할 것

{V1}
    """.strip()
