from __future__ import annotations

import re

from openai import OpenAI
from config import OPENAI_API_KEY
from constants.Model import Model
from prompts.get_gpt_prompt import GptPrompt
from prompts.get_kkk_prompts import KkkPrompt
from utils.query_parser import parse_query
from analyzer.request_문장해체분석기 import get_문장해체


model_name: str = Model.GPT4_1


def kkk_gen(
    user_instructions: str,
    ref: str = "",
) -> str:
    """
    KKK 테스트용 생성 함수 - DB 의존성 제거
    - 프롬프트만 사용하여 원고 생성
    - GptPrompt의 gpt_5_v2_kkk 사용
    
    Returns:
        생성된 원고 텍스트 (str)
        
    Raises:
        RuntimeError: 모델이 빈 응답을 반환한 경우 등
        ValueError: API 키 미설정 등의 환경 이슈
        Exception: OpenAI 호출 실패 등 기타 예외
    """
    
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY가 설정되어 있지 않습니다. .env를 확인하세요.")
    
    print(f"KKK 테스트 시작: {user_instructions}")
    
    parsed = parse_query(user_instructions)
    
    if not parsed["keyword"]:
        raise ValueError("키워드가 없습니다.")
    
    # 참조원고 분석 (gpt_5_v2_service에서 가져온 로직)
    참조분석 = get_문장해체(ref)
    print(f"참조분석 결과: {참조분석}")
    
    # gpt_5_v2_kkk 프롬프트 사용
    기본_프롬프트 = GptPrompt.gpt_5_v2_kkk(
        keyword=parsed["keyword"],
        min_length=1800,
        max_length=2000,
        note=parsed.get("note", "")
    )
    
    # gpt_5_v2_service의 참조원고 분석 프롬프트 구조 차용
    참조_분석_프롬프트 = f"""
[참조원고 분석 데이터 활용 지침]
아래 데이터는 참고 문서에서 추출한 화자/구성/스타일 분석 결과물입니다.  
원고 생성 시 반드시 다음 조건을 반영해야 합니다.

{참조분석}

- "화자 지시"에 따른 인물 설정, 말투, 단어 빈도와 형태소 패턴을 살짝 변형하여 글의 형태만을 따릅니다.  
- "구성 지시"에 따라 서론-중론-결론 흐름을 유지합니다.
- "원고 스타일 세부사항"을 전부 반영해 문체·문단 길이·리듬감·감정선 등을 동일하게 재현합니다.  
- JSON에 기재된 단어/형태소는 반복적으로 등장해야 하며, 실제 경험담+정보 설명이 혼합된 톤을 유지해야 합니다.  

- 부제는 그대로 사용하나 예외 사항은 하단 참조
- 사용자 요청에 (부제X)가 있다면 필수로 숫자만 제거 된 부제 사용
"""
    
    prompt: str = f"""
---

[참조 문서 - KKK 테스트]
- 참조 문서의 업체명은 절대 원고에 포함하지 않습니다.
- 참조 문서와 동일하게 작성하지 않습니다.
- 아래의 분석본과 함께 사용해서 전체적인 흐름을 유사하게 가져갑니다.
- 없다면 넘어갑니다.
{ref}

[참조 원고 분석 - KKK]
{참조_분석_프롬프트}

---

[필수 사항 - KKK 테스트]
{기본_프롬프트}

---

[필수로 이행해야하는 추가 요청 - KKK]
{parsed.get('note', '')}

---
""".strip()
    
    print(f"KKK 테스트 파싱 결과: {parsed}")
    
    client = OpenAI(api_key=OPENAI_API_KEY)
    system = KkkPrompt.get_kkk_system_prompt_v2()
    
    try:
        print(f"KKK GPT 생성 시작 | keyword={user_instructions!r} | model={model_name}")
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {
                    "role": "system", 
                    "content": system,
                },
                {"role": "user", "content": prompt},
            ],
        )
        
        usage = getattr(response, "usage", None)
        if usage is not None:
            in_tokens = getattr(usage, "prompt_tokens", None)
            out_tokens = getattr(usage, "completion_tokens", None)
            total_tokens = getattr(usage, "total_tokens", None)
            print(f"KKK tokens in={in_tokens}, out={out_tokens}, total={total_tokens}")
        
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