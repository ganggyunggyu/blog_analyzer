from __future__ import annotations

import re
from openai import OpenAI

from config import OPENAI_API_KEY
from _constants.Model import Model
from _prompts._private import song_prompt


model_name: str = Model.GPT5_MINI


def song_gen(user_instructions: str, ref: str = "", category: str = "") -> str:
    """
    Generates text using the "song" persona.
    - Reuses songagnes_system_prompt/songagnes_user_prompt from my_service
    - Applies Cain tone by prepending MyPrompt.get_system_prompt() to system
    """

    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY가 설정되어 있지 않습니다. .env를 확인하세요.")

    system = f"""           
{song_prompt.songagnes_system_prompt}
"""

    user = f"""
{song_prompt.songagnes_user_prompt}
---

[유저 입력]

{user_instructions}
"""

    client = OpenAI(api_key=OPENAI_API_KEY)

    try:
        print(f"Song 생성 시작 model={model_name}")
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
            print(f"Song tokens in={in_tokens}, out={out_tokens}, total={total_tokens}")

        choices = getattr(response, "choices", []) or []
        if not choices or not getattr(choices[0], "message", None):
            raise RuntimeError("모델이 유효한 choices/message를 반환하지 않았습니다.")

        text: str = (choices[0].message.content or "").strip()
        if not text:
            raise RuntimeError("모델이 빈 응답을 반환했습니다.")

        # 원본 그대로 반환 (후처리 없음)

        length_no_space = len(re.sub(r"\s+", "", text))
        print(
            f"Song {user_instructions} {model_name} 생성 완료 (공백 제외 길이: {length_no_space})"
        )

        return text

    except Exception as e:
        print("Song OpenAI 호출 실패:", repr(e))
        raise
