from __future__ import annotations
import re

from _constants.Model import Model
from utils.ai_client_factory import call_ai
from utils.query_parser import parse_query
from utils.text_cleaner import comprehensive_text_clean


model_name: str = Model.SOLAR_PRO2


SYSTEM_PROMPT = """"""

USER_PROMPT_TEMPLATE = """
마크다운 금지
피드백 금지 순수
원고만 출력 줄바꿈 필수
{keyword}
"""


def solar_ver3_clean_gen(
    user_instructions: str, ref: str = "", category: str = ""
) -> str:
    parsed = parse_query(user_instructions)
    keyword = parsed.get("keyword", "")
    note = parsed.get("note", "")

    if not keyword:
        raise ValueError("키워드가 없습니다.")

    system = SYSTEM_PROMPT
    user = USER_PROMPT_TEMPLATE.format(keyword=keyword, note=note)

    if ref:
        user = f"{user}\n\n참조 원고:\n{ref}"

    text = call_ai(
        model_name=model_name,
        system_prompt=system,
        user_prompt=user,
    )

    text = comprehensive_text_clean(text)

    length_no_space = len(re.sub(r"\s+", "", text))


    return text
