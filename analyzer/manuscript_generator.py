import os
from openai import OpenAI
import json
from config import OPENAI_API_KEY
from mongodb_service import MongoDBService
from prompts.get_ko_prompt import getKoPrompt
from prompts.get_my_ko_prompt import myGetKoPrompt
from prompts.get_ref import ref
from typing import Optional


def generate_manuscript_with_ai(
    unique_words: list,
    sentences: list,
    expressions: dict,
    parameters: dict,
    user_instructions: str
) -> str:
    """
    수집된 분석 데이터를 기반으로 OpenAI API를 사용하여 블로그 원고를 생성합니다.
    """
    if not OPENAI_API_KEY:
        raise ValueError("API 키가 설정되지 않았습니다. .env 파일에 OPENAI_API_KEY를 추가해주세요.")
    client = OpenAI(api_key=OPENAI_API_KEY)

    words_str = ", ".join(unique_words) if unique_words else "없음"
    sentences_str = "\n- ".join(sentences) if sentences else "없음"
    expressions_str = json.dumps(expressions, ensure_ascii=False, indent=2) if expressions else "없음"
    parameters_str = json.dumps(parameters, ensure_ascii=False, indent=2) if parameters else "없음"

    prompt = f"""

    [고유 단어 리스트]
    {words_str}

    [문장 리스트]
     - {sentences_str}
    
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

    """

    try:
        response = client.chat.completions.create(
            model='gpt-5-mini-2025-08-07',
            # model='gpt-5-nano-2025-08-07',
            # model='gpt-4.1-2025-04-14', 
            messages=[
                {"role": "system", "content": "You are a professional blog post writer. Your task is to generate a blog post based on provided analysis data and user instructions."},
                {"role": "user", "content": prompt}
            ],
            # temperature=0.2,
            
        )
        usage = response.usage
        print(f"사용된 토큰 수 - prompt: {usage.prompt_tokens}, completion: {usage.completion_tokens}, total: {usage.total_tokens}")

        generated_manuscript = response.choices[0].message.content.strip()

        return generated_manuscript
    except Exception as e:
        print(f"OpenAI API 호출 중 오류가 발생했습니다: {e}")
        raise
    

    

