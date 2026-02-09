"""Grok 한려담원 유저 프롬프트 템플릿"""

from _prompts.rules.line_break_rules import line_break_rules
from _prompts.rules.emphasis_rules import NO_FOREIGN_LANGUAGE, DIVERSE_ENDING
from _prompts.common.ver1 import V1


def get_grok_hanryeo_user_prompt(keyword: str, note: str, ref: str) -> str:
    """Grok 한려담원 유저 프롬프트 생성"""
    return f"""

키워드: {keyword}
---
추가 요청: ({note})

# 줄바꿈 지침
{line_break_rules}
{NO_FOREIGN_LANGUAGE}

{DIVERSE_ENDING}

추가 요청은 어떤일이 있어도 최우선으로 지켜져야 합니다.

---
참조 원고: {ref}
- 참조원고가 있다면?: 참조원고의 내용의 흐름을 따라 그대로 작성할 것

{V1}

---

# 한려담원 추천 규칙
- 키워드 정보를 충분히 전달한 후 (글의 70% 이상)
- 글 후반부에서 자연스럽게 흑염소/한려담원 언급
- 제품 특징은 2~3가지만 간결하게
- "제가 알아본 제품은 한려담원 흑염소예요" 톤
- 환불 정책으로 부담 없이 시작할 수 있다는 마무리
    """.strip()
