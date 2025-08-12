# utils/gemini_client.py
from typing import Optional
import json
from config import GEMINI_API_KEY
from prompts.get_ko_prompt import getKoPrompt
import re
from google import genai
from google.genai import types

def get_gemini_response(
    unique_words: list,
    sentences: list,
    expressions: dict,
    parameters: dict,
    user_instructions: str,
    ref: str = "",
    *,
    model: str = "gemini-2.5-flash",
    max_output_tokens: int = 1900,
    temperature: float = 0.2,
    top_p: float = 0.95,
    system_prompt: Optional[str] = "You are a professional blog post writer. Your task is to generate a blog post based on provided analysis data and user instructions."
) -> str:
    """
    Gemini로 원고 생성 (재시도 없음). Claude/OpenAI와 동일한 프롬프트 형태 사용.
    반환: 생성 텍스트(없으면 빈 문자열)
    [고유 단어 리스트]
    {words_str}s
    [문장 리스트]
    - {sentences_str}
    """
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY가 설정되지 않았습니다.")

    # --- 프롬프트 구성 ---
    words_str = ", ".join(unique_words) if unique_words else "없음"
    sentences_str = "\n- ".join(sentences) if sentences else "없음"
    expressions_str = json.dumps(expressions, ensure_ascii=False, indent=2) if expressions else "없음"
    parameters_str = json.dumps(parameters, ensure_ascii=False, indent=2) if parameters else "없음"

    user_prompt = f"""


    

    [표현 라이브러리 (중분류 키워드: [표현])]
    {expressions_str}

    [AI 개체 인식 및 그룹화 결과 (대표 키워드: [개체])]
    {parameters_str}

    [사용자 지시사항]
    {user_instructions}

    [참고 문서]
    {ref}

    [요청]
    {getKoPrompt(keyword=user_instructions)}

    [문서의 길이확인 필수]
    - 한국어 기준 공백 제거 후 1,999 단어 이상 검수가 필요합니다.
    - 만약 모자랄 경우 다시 제작해야합니다.

    [필수 확인사항]
    - 절대 문장이 중간에 끊겨서는 안됩니다.
    - 완벽하게 마무리가 된 문장 형태여야만합니다.
    """.strip()

    

    # ... (기존 코드)

    try:
        client = genai.Client(api_key=GEMINI_API_KEY)

        res = client.models.generate_content(
            model=model,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=temperature,
                top_p=top_p,
                # max_output_tokens=max_output_tokens,
            ),
            contents=user_prompt,
        )
        
        # 토큰 사용량 정보 추가
        input_tokens = res.usage_metadata.prompt_token_count
        output_tokens = res.usage_metadata.candidates_token_count
        
        print(f'입력 토큰 수: {input_tokens}')
        print(f'출력 토큰 수: {output_tokens}')
        print(f'총 토큰 수: {input_tokens + output_tokens}')

        # 기존 텍스트 길이 출력
        length_no_space = len(re.sub(r"\s+", "", res.text))
        print(f'gemini 문서 생성 완료 (공백 제외 길이: {length_no_space})')

        return res.text

    except Exception as e:
        print(f"An error occurred: {e}")
        return f"An error occurred: {e}"