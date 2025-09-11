from __future__ import annotations

import re
from openai import OpenAI
import time

from _prompts._private.gang_prompt import gang_prompt
from config import OPENAI_API_KEY
from _constants.Model import Model


model_name: str = Model.GPT5


def gang_gen(user_instructions: str, ref: str = "", category: str = "") -> str:
    """
    Generates text using the "gang" persona.
    - Reuses gang_prompt from my_service
    - Applies Cain tone by prepending MyPrompt.get_system_prompt() to system
    """

    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY가 설정되어 있지 않습니다. .env를 확인하세요.")

    system = f"""
{gang_prompt}
"""

    user = f"""
{gang_prompt}
[유저 입력]

{user_instructions}
"""

    client = OpenAI(api_key=OPENAI_API_KEY)

    try:
        start_ts = time.time()
        print("원고작성 시작")
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )

        usage = getattr(response, "usage", None)
        if usage is not None:
            in_tokens = getattr(usage, "prompt_tokens", None)
            out_tokens = getattr(usage, "completion_tokens", None)
            total_tokens = getattr(usage, "total_tokens", None)
            print(f"Gang tokens in={in_tokens}, out={out_tokens}, total={total_tokens}")

        choices = getattr(response, "choices", []) or []
        if not choices or not getattr(choices[0], "message", None):
            raise RuntimeError("모델이 유효한 choices/message를 반환하지 않았습니다.")

        text: str = (choices[0].message.content or "").strip()
        if not text:
            raise RuntimeError("모델이 빈 응답을 반환했습니다.")

        # 원본 그대로 반환 (후처리 없음)

        length_no_space = len(re.sub(r"\s+", "", text))
        print(f"원고 길이 체크: {length_no_space}")
        elapsed = time.time() - start_ts
        print(f"원고 소요시간: {elapsed:.2f}s")
        print("원고작성 완료")

        return text

    except Exception as e:
        print("Gang OpenAI 호출 실패:", repr(e))
        raise
