from __future__ import annotations
import re

from openai import OpenAI
from config import OPENAI_API_KEY
from _constants.Model import Model


model_name: str = Model.GPT5_MINI

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
- 한 줄은 30자를 넘기지 않도록 작성  
- 한 줄은 가급적 약 25자 이후 자연스럽게 줄바꿈  
- {{소제목}} 하단은 줄바꿈 두 번  
- 앞에 {{숫자}}. 으로 시작하는 {{소제목}}은 줄바꿈 금지  
- 2~3줄마다 줄바꿈  
- 한 문단은 3~5줄 유지  
- 짧은 문장을 마구 끊지 않고 자연스러운 리듬으로 작성  
- 모든 한 줄은 일정한 길이로 출력하며, 우측 공백 금지  
- 문단 글자수 규칙을 딱딱 준수하는 것도 중요하지만 문장의 균형감과 가독성이 더 중요해
- 자연스럽게 ㅋㅋㅋ ㅎㅎ ㅜㅜ !! 같은 표현이나 이모지를 넣어줘도돼 너무 많이 말고 포인트만

"""

    """
    프롬프트 보관

    - 마크다운 절대 추가 금지 (--- 절대 금지 채팅 끊긴다고)
    - 마크다운 문법(#, *, -, ``` 등) 절대 사용 금지
    """

    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {
                    "role": "system",
                    "content": "당신은 원본의 글을 절대 변형하지 않으면서 깔끔하게 문단정리 및 줄바꿈를 해주는 도우미 입니다.",
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

        choices = getattr(response, "choices", []) or []
        if not choices or not getattr(choices[0], "message", None):
            raise RuntimeError("모델이 유효한 choices/message를 반환하지 않았습니다.")

        text: str = re.sub(
            r"\n마무리 멘트.*$",
            "",
            re.sub(
                r"(?s)^서론.*?1\.", "1.", (choices[0].message.content or "").strip()
            ),
            flags=re.S,
        ).strip()

        if not text:
            raise RuntimeError("모델이 빈 응답을 반환했습니다.")

        return text

    except Exception:
        raise
