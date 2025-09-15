from __future__ import annotations
import re
import time

from openai import OpenAI
from config import OPENAI_API_KEY
from _constants.Model import Model
from _prompts.get_kkk_prompts import KkkPrompt
from _prompts.service.get_ref_prompt import get_ref_prompt
from utils.format_paragraphs import format_paragraphs
from utils.query_parser import parse_query
from utils.text_cleaner import comprehensive_text_clean


model_name: str = Model.GPT4_1
min_length: int
max_length: int

client = OpenAI(api_key=OPENAI_API_KEY)


def kkk_gen(user_instructions: str, ref: str = "", category: str = "") -> str:
    """
    Returns:
        생성된 원고 텍스트 (str)

    Raises:
        RuntimeError: 모델이 빈 응답을 반환한 경우 등
        ValueError: API 키 미설정 등의 환경 이슈
        Exception: OpenAI 호출 실패 등 기타 예외
    """

    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY가 설정되어 있지 않습니다. .env를 확인하세요.")

    parsed = parse_query(user_instructions)

    if not parsed["keyword"]:
        raise ValueError("키워드가 없습니다.")

    # if category == "legalese":
    #     model_name = Model.GPT5
    # else:
    #     model_name = Model.GPT5_CHAT

    if model_name == Model.GPT5_CHAT:
        min_length, max_length = 3000, 3200
    elif model_name == Model.GPT5:
        min_length, max_length = 2200, 2400
    else:
        min_length, max_length = 2500, 2600

    기본_프롬프트 = KkkPrompt.kkk_prompt_gpt_5(
        keyword=parsed["keyword"],
        min_length=min_length,
        max_length=max_length,
        note=parsed.get("note", ""),
        category=category,
    )
    참조_분석_프롬프트 = get_ref_prompt(ref)

    system = KkkPrompt.get_kkk_system_prompt_v2()

    user: str = (
        f"""
{system}
---

[참조 원고 분석]
{ref}
{참조_분석_프롬프트}

---

[필수 사항]
{기본_프롬프트}

---

[필수로 이행해야하는 추가 요청]
{parsed.get('note', '')}

---
""".strip()
    )

    try:
        start_ts = time.time()
        is_ref = len(ref) != 0
        print(
            f"[GEN] service={'test-kkk'} | model={model_name} | category={category} | keyword={user_instructions} | is_ref={is_ref}"
        )
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {
                    "role": "system",
                    "content": system,
                },
                {
                    "role": "user",
                    "content": user,
                },
            ],
        )

        usage = getattr(response, "usage", None)
        if usage is not None:
            in_tokens = getattr(usage, "prompt_tokens", None)
            out_tokens = getattr(usage, "completion_tokens", None)
            total_tokens = getattr(usage, "total_tokens", None)
            print(
                f"[🔍 Token Usage] "
                f"Prompt: {in_tokens:,}  |  "
                f"Completion: {out_tokens:,}  |  "
                f"Total: {total_tokens:,}"
            )
        choices = getattr(response, "choices", []) or []
        if not choices or not getattr(choices[0], "message", None):
            raise RuntimeError("모델이 유효한 choices/message를 반환하지 않았습니다.")

        text: str = (choices[0].message.content or "").strip()
        if not text:
            raise RuntimeError("모델이 빈 응답을 반환했습니다.")

        text = format_paragraphs(text)
        text = comprehensive_text_clean(text)

        length_no_space = len(re.sub(r"\s+", "", text))
        elapsed = time.time() - start_ts
        print(f"원고 길이 체크: {length_no_space}")
        print(f"원고 소요시간: {elapsed:.2f}s")
        print("원고작성 완료")

        return text

    except Exception as e:
        raise
