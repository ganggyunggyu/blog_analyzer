"""프롬프트 없는 Clean DeepSeek 서비스"""

from __future__ import annotations
import re
import time

from _constants.Model import Model
from _prompts.category import 맛집
from utils.query_parser import parse_query
from utils.text_cleaner import comprehensive_text_clean
from utils.ai_client_factory import call_ai


MODEL_NAME: str = Model.DEEPSEEK_CHAT


def clean_deepseek_gen(
    user_instructions: str, ref: str = "", category: str = ""
) -> str:
    """프롬프트 없이 유저 입력만으로 생성"""
    parsed = parse_query(user_instructions)
    keyword = parsed.get("keyword", "")
    note = parsed.get("note", "") or ""

    if not keyword:
        raise ValueError("키워드가 없습니다.")

    system_prompt = ""

    user_prompt = f"""
키워드: {keyword}

추가 요청: {note}

참조 원고: {ref}

{맛집}


2000단어 이상 작성
마크다운 문법 금지

## 줄바꿈 지침
- 목적: 텍스트 가독성 향상 위해 적절한 줄바꿈 위치 지정
- 한줄 줄바꿈 타이밍: 한 줄당 30~35자로 제한 (모바일 가독성을 위한 자연스러운 줄바꿈)
- 두줄 줄바꿈 타이밍: 1줄마다 \\n\\n으로 **두번** 줄바꿈 해서 텍스트 띄우기


### 한줄 줄바꿈 예시:
안녕하세요 이건
한줄 줄바꿈 예시입니다.

### 두줄 줄바꿈 예시:
안녕하세요 이건
두줄 줄바꿈 예시입니다.
(공백)  
이렇게 한 문단별로 줄바꿈을
이행하시면 됩니다.


## 출력예시:

### 예시:

드디어 셀레네하우스에서 본식을 올렸어요.
작년 가을, 비가 살짝 왔지만
야외 포토존 덕에 분위기 업!

메리다 투어 때 느꼈던 바쁜 느낌 없이
4시간 동안 여유롭게 진행됐어요.

식순은 1부 포멀 예식으로 시작해
샌드 세레머니를 넣었는데,
하객분들 '새롭다' 하시며 박수 쳐주셨어요.
""".strip()

    try:
        start_time = time.time()
        print(f"[Clean DeepSeek] 서비스: {category}")
        print(f"[Clean DeepSeek] 키워드: {keyword}")
        print("[Clean DeepSeek] 원고작성 시작")

        generated_text = call_ai(
            model_name=MODEL_NAME,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )

        cleaned_text = comprehensive_text_clean(generated_text)

        char_count_no_space = len(re.sub(r"\s+", "", cleaned_text))
        elapsed_time = time.time() - start_time

        print(f"[Clean DeepSeek] 원고 길이: {char_count_no_space}")
        print(f"[Clean DeepSeek] 소요시간: {elapsed_time:.2f}s")
        print("[Clean DeepSeek] 완료")

        return cleaned_text

    except Exception as api_error:
        print(f"[Clean DeepSeek] API 오류: {api_error}")
        raise api_error
