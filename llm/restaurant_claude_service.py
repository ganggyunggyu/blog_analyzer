"""맛집 Claude 서비스"""

from __future__ import annotations
import re
import time

from anthropic._exceptions import BadRequestError, RateLimitError

from _constants.Model import Model
from utils.query_parser import parse_query
from utils.text_cleaner import comprehensive_text_clean
from utils.ai_client_factory import call_ai


MODEL_NAME: str = Model.CLAUDE_OPUS_4_5


def restaurant_claude_gen(user_instructions: str, ref: str = "", category: str = "") -> str:
    """맛집 전용 Claude 생성"""
    parsed = parse_query(user_instructions)
    keyword = parsed.get("keyword", "")
    note = parsed.get("note", "") or ""

    if not keyword:
        raise ValueError("키워드가 없습니다.")

    # 시스템 프롬프트 없음 (빈 문자열)
    system_prompt = ""

    # 유저 프롬프트 = 키워드 + 노트 + 참조원고만
    user_prompt = f"""
키워드: {keyword}

추가 요청: {note}

참조 원고: {ref}

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

---

## 사용 방법

### 입력 형식
```
키워드: [작성할 키워드]
카테고리: [맛집/일반/건강 등]
추가 요청: [특별 요청사항이 있다면 기재]
참조 원고: [참조할 원고가 있다면 첨부]
```

### 참조 원고가 있는 경우
참조 원고의 내용 흐름을 따라 그대로 작성

### 키워드가 3단어 이상인 경우
유저가 지정한 제목으로 간주하여 해당 제목 사용
""".strip()

    try:
        start_time = time.time()
        print(f"[맛집 Claude] 서비스: {category}")
        print(f"[맛집 Claude] 키워드: {keyword}")
        print("[맛집 Claude] 원고작성 시작")

        generated_text = call_ai(
            model_name=MODEL_NAME,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )

        cleaned_text = comprehensive_text_clean(generated_text)

        char_count_no_space = len(re.sub(r"\s+", "", cleaned_text))
        elapsed_time = time.time() - start_time

        print(f"[맛집 Claude] 원고 길이: {char_count_no_space}")
        print(f"[맛집 Claude] 소요시간: {elapsed_time:.2f}s")
        print("[맛집 Claude] 완료")

        return cleaned_text

    except (BadRequestError, RateLimitError) as api_error:
        print(f"[맛집 Claude] API 오류: {api_error}")
        raise api_error
