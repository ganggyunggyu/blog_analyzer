from __future__ import annotations
import re

from openai import OpenAI
from config import OPENAI_API_KEY
from _constants.Model import Model
from _prompts.get_gpt_prompt import GptPrompt
from _prompts.get_kkk_prompts import KkkPrompt
from _prompts.service.get_ref_prompt import get_ref_prompt
from _prompts.service.get_mongo_prompt import get_mongo_prompt
from utils.query_parser import parse_query


model_name: str = Model.GPT4_1

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

    print(f"KKK Service {user_instructions}")

    parsed = parse_query(user_instructions)

    if not parsed["keyword"]:
        raise ValueError("키워드가 없습니다.")

    기본_프롬프트 = KkkPrompt.kkk_prompt_gpt_5(
        keyword=parsed["keyword"],
        note=parsed.get("note", ""),
    )
    참조_분석_프롬프트 = get_ref_prompt(ref)

    system = KkkPrompt.get_kkk_system_prompt_v2(category)

    # _mongo_data = get_mongo_prompt()

    user: str = (
        f"""

{system}

---
[참조 문서]
- 참조 문서의 업체명은 절대 원고에 포함하지 않습니다.
- 참조 문서와 동일하게 작성하지 않습니다.
- 아래의 분석본과 함께 사용해서 전체적인 흐름과 화자의 어투를 유사하게 가져갑니다.
- 없다면 넘어갑니다.

{ref}

[참조 원고 분석]
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

    print(f"KKK Service 파싱 결과: {parsed}")
    # print(참조_분석_프롬프트)

    try:
        print(f"KKK GPT 생성 시작 | keyword={user_instructions!r} | model={model_name}")
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
                f"KKK Service tokens in={in_tokens}, out={out_tokens}, total={total_tokens}"
            )

        choices = getattr(response, "choices", []) or []
        if not choices or not getattr(choices[0], "message", None):
            raise RuntimeError("모델이 유효한 choices/message를 반환하지 않았습니다.")

        text: str = (choices[0].message.content or "").strip()
        if not text:
            raise RuntimeError("모델이 빈 응답을 반환했습니다.")

        length_no_space = len(re.sub(r"\s+", "", text))
        print(f"KKK {model_name} 문서 생성 완료 (공백 제외 길이: {length_no_space})")

        return text

    except Exception as e:
        print("KKK OpenAI 호출 실패:", repr(e))
        raise
