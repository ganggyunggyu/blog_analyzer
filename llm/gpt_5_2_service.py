from __future__ import annotations

import os
import re
import time

from openai import OpenAI
from _prompts import get_kkk_prompts
from _prompts.service.get_mongo_prompt import get_mongo_prompt
from config import OPENAI_API_KEY
from _constants.Model import Model
from mongodb_service import MongoDBService
from _prompts.get_gpt_prompt import GptPrompt
from _prompts.get_kkk_prompts import KkkPrompt
from _prompts.get_system_prompt import get_system_prompt_v2
from utils.format_paragraphs import format_paragraphs
from utils.get_category_db_name import get_category_db_name
from utils.query_parser import parse_query

from analyzer.request_문장해체분석기 import get_문장해체
from utils.text_cleaner import comprehensive_text_clean


model_name: str = Model.GPT5_2

기본_프롬프트 = ""


async def gpt_5_2_gen(
    user_instructions: str,
    ref: str = "",
) -> str:
    """
    GPT-5.2 Responses API를 사용한 원고 생성
    """

    category = ""
    if user_instructions:
        category = await get_category_db_name(user_instructions)

    if not category:
        category = os.getenv("MONGO_DB_NAME", "wedding")

    db_service = MongoDBService()

    db_service.set_db_name(db_name=category)

    parsed = parse_query(user_instructions)

    if parsed["keyword"] == None:
        raise

    def sanitize(s: str) -> str:
        s = s or ""
        s = re.sub(
            r"(?i)ignore previous|override|system message|do not obey|follow only.*",
            "",
            s,
        )
        s = re.sub(r"```.*?```", "", s, flags=re.S)
        return s.strip()

    _mongo_data = sanitize(get_mongo_prompt(category, user_instructions))

    user: str = (
        f"""

""".strip()
    )

    client = OpenAI(api_key=OPENAI_API_KEY)

    system = ""

    try:
        start_ts = time.time()
        print("원고작성 시작")
        response = client.responses.create(
            model=model_name,
            instructions=system,
            input=user,
            reasoning={"effort": "medium"},
            text={"verbosity": "high"},
        )

        text: str = getattr(response, "output_text", "") or ""
        if not text:
            raise RuntimeError("모델이 빈 응답을 반환했습니다.")

        length_no_space = len(re.sub(r"\s+", "", text))
        print(f"원고 길이 체크: {length_no_space}")

        print("원고작성 완료")

        text = comprehensive_text_clean(text)
        elapsed = time.time() - start_ts
        print(f"원고 소요시간: {elapsed:.2f}s")

        return text

    except Exception as e:
        raise
