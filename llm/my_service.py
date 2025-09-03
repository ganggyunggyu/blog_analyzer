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

    print(f"My Service {user_instructions}")

    parsed = parse_query(user_instructions)

    if not parsed["keyword"]:
        raise ValueError("키워드가 없습니다.")

    system = MyPrompt.get_system_prompt()
    user = MyPrompt.get_user_prompt()

    print(f"My Service 파싱 결과: {parsed}")

    prompt = f"""
{user}
{user_instructions}
"""

    try:
        print(f"My GPT 생성 시작 | keyword={user_instructions!r} | model={model_name}")
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
