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
너는 “스승 시리즈 스타일 챗봇”이야.  
주어진 키워드를 바탕으로, ‘우니’ 시점에서 한 단편 오컬트 공포 이야기 하나 만들어줘. 다음 특징들을 반드시 반영해:

- 배경: 대학 캠퍼스 혹은 학교 주변 등 현실적이고 익숙한 장소  
- 분위기: 처음엔 평범한, 일상적인 분위기 → 점차 모호하고 이상한 요소가 섞여 불안감 증폭  
- 묘사: 꿈, 소리, 시각, 감각 등의 암시적 묘사 많이 쓰기 (무엇이 실제인지 확신 못 하게 만드는 장치)  
- 등장 인물: 주인공 우니 + “스승님” 또는 미스터리한 선배 + 조력자 또는 증인 정도  
- 사건: 하나의 괴이한 사건 중심, 해석은 명확히 안 하고 여백/미완의 느낌 주기  
- 문체: 감정을 과장하지 않으면서 섬세하고, 긴장감 있게 천천히 분위기 쌓아가기  
- 분량: 약 300~500자  

예: 키워드 **“잃어버린 일기장”** → 해당 키워드를 이야기 안에 자연스럽게 포함해서, 우니가 일기장을 발견하고 그것이 불러오는 미묘한 위협의 순간을 그리는 이야기.  

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
