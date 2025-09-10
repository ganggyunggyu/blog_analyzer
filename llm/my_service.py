from __future__ import annotations
import re

from openai import OpenAI
import time
from config import OPENAI_API_KEY
from _constants.Model import Model
from utils.format_paragraphs import format_paragraphs
from utils.text_cleaner import comprehensive_text_clean


model_name: str = Model.GPT5

client = OpenAI(api_key=OPENAI_API_KEY)


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

    prompt = f"""

{user_instructions}

- 키워드: ({user_instructions})

[지시사항]
- 키워드 및 참조원고 기반의 블로그 원고 작성
- 글자 수 공백 제외 {2000}~{2300}자 사이를 (필수)로 지켜야합니다.

[추가 요청사항]

- 이 부분은 유저가 추가로 요청하는 부분으로 반드시 이행 되어야 합니다.

마크다운쳐쓰지말라고좀
"""

    try:
        start_ts = time.time()
        print("원고작성 시작")
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {
                    "role": "system",
                    "content": prompt,
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
        print(f"원고 길이 체크: {length_no_space}")
        elapsed = time.time() - start_ts
        print(f"원고 소요시간: {elapsed:.2f}s")
        print("원고작성 완료")

        return text

    except Exception as e:
        print("My OpenAI 호출 실패:", repr(e))
        raise
