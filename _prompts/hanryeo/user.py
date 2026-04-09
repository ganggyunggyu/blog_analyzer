"""한려담원 - User Prompt v4.3

키워드 + 네이버 뷰탭 기반 제목 변수 믹스 주입
"""

import random

from _prompts.hanryeo.title_variables import build_title_pattern_mix_block


def get_hanryeo_user_prompt(
    keyword: str,
    category: str = "",
    note: str = "",
    ref: str = "",
    rng: random.Random | None = None,
) -> str:
    """한려담원 유저 프롬프트 생성 (v4.3)"""

    rng = rng or random.Random()
    title_style_block = build_title_pattern_mix_block(keyword=keyword, rng=rng)
    no_comma = rng.random() < 0.7

    comma_rule = (
        "제목에 쉼표(,)를 사용하지 마세요."
        if no_comma
        else "제목에 쉼표를 사용해도 됩니다."
    )

    prompt = f"""━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[키워드]: {keyword}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{title_style_block}

[제목 추가 규칙]
{comma_rule}"""

    if note:
        prompt += f"\n\n[추가 요청사항]\n{note}"

    if ref:
        prompt += (
            "\n\n[참조 원고]\n"
            "아래 자료는 참고용입니다. 문장을 그대로 베끼지 말고,"
            " 정보 흐름과 마무리 리듬만 참고하세요.\n\n"
            f"{ref}"
        )

    return prompt.strip()
