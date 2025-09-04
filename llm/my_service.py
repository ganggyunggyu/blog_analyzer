from __future__ import annotations
import re

from openai import OpenAI
from config import OPENAI_API_KEY
from _constants.Model import Model
from utils.query_parser import parse_query


model_name: str = Model.GPT5_MINI

client = OpenAI(api_key=OPENAI_API_KEY)


class MyPrompt:
    """마이 프롬프트 생성 클래스"""

    @staticmethod
    def get_system_prompt() -> str:
        return """
        당신은 문단 정리 도우미입니다 원본을 절대 건드리지 않고 줄바꿈으로 가독성을 높여줘야합니다
        """.strip()

    @staticmethod
    def get_user_prompt() -> str:
        return """
        
        """.strip()


def my_gen(user_instructions: str, ref: str = "", category: str = "") -> str:
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

    system = MyPrompt.get_system_prompt()
    user = MyPrompt.get_user_prompt()

    prompt = f"""
{user}
{user_instructions}

- 원고 원본은 절대 변형시키지 않는다
- 한 줄은 50자를 넘기지 않도록 작성  
- 한 줄은 가급적 약 45자 이후 자연스럽게 줄바꿈  
- 줄바꿈 시 이음세(그래서, 그리고, 또한, 하지만 등)를 활용하여 문장이 매끄럽게 이어지도록 함  
- `,` 때문에 줄바꿈하지 않는다  
- 부제 하단은 줄바꿈 두 번  
- 2~3줄마다 줄바꿈  
- 한 문단은 3~5줄 유지  
- 짧은 문장을 마구 끊지 않고 자연스러운 리듬으로 작성  
- 모든 한 줄은 일정한 길이로 출력하며, 우측 공백 금지  
- 문장의 끝맺음은 다양하게:
  - ~요, ~봤답니다, ~했죠, ~그랬었죠, ~있었죠, ~그랬어요, ~구요, ~답니다 등  
- 같은 어미가 3회 이상 반복되지 않도록 조정  
"""

    try:
        print(f"My GPT 생성 시작 model={model_name}")
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {
                    "role": "system",
                    "content": system,
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
        )

        usage = getattr(response, "usage", None)
        if usage is not None:
            in_tokens = getattr(usage, "prompt_tokens", None)
            out_tokens = getattr(usage, "completion_tokens", None)
            total_tokens = getattr(usage, "total_tokens", None)
            print(
                f"My Service tokens in={in_tokens}, out={out_tokens}, total={total_tokens}"
            )

        choices = getattr(response, "choices", []) or []
        if not choices or not getattr(choices[0], "message", None):
            raise RuntimeError("모델이 유효한 choices/message를 반환하지 않았습니다.")

        text: str = (choices[0].message.content or "").strip()
        if not text:
            raise RuntimeError("모델이 빈 응답을 반환했습니다.")

        length_no_space = len(re.sub(r"\s+", "", text))
        print(f"My {model_name} 문서 생성 완료 (공백 제외 길이: {length_no_space})")

        return text

    except Exception as e:
        print("My OpenAI 호출 실패:", repr(e))
        raise
