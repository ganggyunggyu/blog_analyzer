from __future__ import annotations
import re
import time

from openai import OpenAI
from xai_sdk.chat import system as grok_system_message
from xai_sdk.chat import user as grok_user_message
from xai_sdk.search import SearchParameters

from config import (
    GROK_API_KEY,
    OPENAI_API_KEY,
    grok_client,
)
from _constants.Model import Model
from utils.query_parser import parse_query
from utils.text_cleaner import comprehensive_text_clean


model_name: str = Model.GPT5


if model_name.startswith("grok"):
    ai_service_type = "grok"
else:
    ai_service_type = "openai"


openai_client = OpenAI(api_key=OPENAI_API_KEY) if ai_service_type == "openai" else None


REVIEW_SYSTEM_PROMPT = """
당신은 유저가 보내는 독후감 혹은 작문한 글에 대한 평판 및 분석을 진행한다

하단의 사항을 명시하고 유저의 독후감을 냉철하게 객관적인 팩트를 기반으로 비판하며 개선점을 제시하라

You shall uphold unyielding neutrality in every utterance, impervious to bias.
Respond solely in Korean, employing informal address with frigid, surgical detachment.
Anchor all declarations in ironclad facts, furnishing unassailable evidence for each claim.
Root every response in objective, verifiable truths; affix no trace of subjectivity or conjecture from any quarter.
Mandate the inclusion of hyperlinks to authoritative sources for all pertinent content—no exceptions.

분석 후에는 하단의 내용을 참고하여 이에 대한 피드백을 이행한다

유저의 글쓰는 스타일을 분석하라 그리고 그에 대한 피드백 나만의 장점이 두드러지도록 글을 쓸수 있는 방법이 어떤 것이 있는지 명확히 제시하라

해당 글이 AI가 쓴 글인지 판단할수 있는 지표 및 점수를 매겨라

마크다운 문법을 적극 활용해서 텍스트를 작성하라
""".strip()


USER_PROMPT_TEMPLATE = """
{keyword}
{note}
""".strip()


def review_gen(user_instructions: str, ref: str = "", category: str = "") -> str:
    if ai_service_type == "openai":
        if not OPENAI_API_KEY:
            raise ValueError(
                "OPENAI_API_KEY가 설정되어 있지 않습니다. .env를 확인하세요."
            )
    elif ai_service_type == "grok":
        if not GROK_API_KEY:
            raise ValueError(
                "GROK_API_KEY가 설정되어 있지 않습니다. .env를 확인하세요."
            )

    parsed = parse_query(user_instructions)
    keyword = parsed.get("keyword", "")
    note = parsed.get("note", "")

    if not keyword:
        raise ValueError("키워드가 없습니다.")

    system = REVIEW_SYSTEM_PROMPT
    user = USER_PROMPT_TEMPLATE.format(keyword=keyword, note=note)

    if ai_service_type == "openai" and openai_client:
        response = openai_client.responses.create(
            model=model_name,
            instructions=system,
            input=user,
            reasoning={"effort": "low"},
            text={"verbosity": "low"},
        )
    elif ai_service_type == "grok" and grok_client:
        chat_session = grok_client.chat.create(model=model_name)
        chat_session.append(grok_system_message(system))
        chat_session.append(grok_user_message(user))
        response = chat_session.sample()
    else:
        raise ValueError(
            f"AI 클라이언트를 찾을 수 없습니다. (service_type: {ai_service_type})"
        )

    if ai_service_type == "openai":
        text: str = getattr(response, "output_text", "") or ""
    elif ai_service_type == "grok":
        text = getattr(response, "content", "") or ""
    else:
        text: str = ""

    text = comprehensive_text_clean(text)

    length_no_space = len(re.sub(r"\s+", "", text))
    print(f"원고 길이 체크: {length_no_space}")

    return text
