from __future__ import annotations
import re

from openai import OpenAI
from _rule import SEN_RULES
from config import OPENAI_API_KEY
from _constants.Model import Model
from utils.query_parser import parse_query


model_name: str = Model.GPT5

client = OpenAI(api_key=OPENAI_API_KEY)


def format_paragraphs(doc: str) -> str:
    """
    문단정리
    """

    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY가 설정되어 있지 않습니다. .env를 확인하세요.")

    prompt = f"""
# 기존 글

{doc}

---

# 문장 구조 지침 

- 기존 글을 아래의 규칙에 따라 문단정리 및 줄바꿈을 한다
- 기존 글을 절대 변형하지 않는다
- 한 줄은 50자를 넘기지 않도록 작성  
- 한 줄은 가급적 약 45자 이후 자연스럽게 줄바꿈  
- 줄바꿈 시 이음세 부분을(그래서, 그리고, 또한, 하지만 등)를 활용하여 문장이 매끄럽게 이어지도록 함  
- `,` 때문에 줄바꿈하지 않는다  
- 부제 하단은 줄바꿈 두 번  
- 2~3줄마다 줄바꿈  
- 한 문단은 3~5줄 유지  
- 짧은 문장을 마구 끊지 않고 자연스러운 리듬으로 작성  
- 모든 한 줄은 일정한 길이로 출력하며, 우측 공백 금지  
- 마크다운 절대 추가 금지 (--- 절대 금지 채팅 끊긴다고)
- 마크다운 문법(#, *, -, ``` 등) 절대 사용 금지
- 만약 원고 본문 말고 다른 내용이 있다면 지워줘
- 문단 글자수 규칙을 딱딱 준수하는 것도 중요하지만 문장의 균형감과 가독성이 더 중요해

"""

    try:
        print("원고검토 시작")
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {
                    "role": "system",
                    "content": "당신은 원본의 글을 절대 변형하지 않으면서 깔끔하게 문단정리 및 줄바꿈을 해주면서 원고의 규칙에 어긋나는 부분이 있다면 고쳐주는 도우미 입니다.",
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
                f"줄바꿈 tokens in={in_tokens}, out={out_tokens}, total={total_tokens}"
            )

        choices = getattr(response, "choices", []) or []
        if not choices or not getattr(choices[0], "message", None):
            raise RuntimeError("모델이 유효한 choices/message를 반환하지 않았습니다.")

        text: str = (choices[0].message.content or "").strip()
        if not text:
            raise RuntimeError("모델이 빈 응답을 반환했습니다.")

        print("줄바꿈 완료")

        return text

    except Exception as e:
        print("My OpenAI 호출 실패:", repr(e))
        raise
