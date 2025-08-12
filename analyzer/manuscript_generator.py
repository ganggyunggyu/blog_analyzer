import re
import json
from openai import OpenAI
from config import OPENAI_API_KEY
from prompts.get_ko_prompt import getKoPrompt
from utils.text_len import length_no_space, is_len_between
from constants.Model import Model

async def generate_manuscript_with_ai(
    unique_words: list,
    sentences: list,
    expressions: dict,
    parameters: dict,
    user_instructions: str,
    ref: str = '',
    min_length_no_space: int = 1700,
    max_length_no_space: int = 2000,
    max_retry: int = 5
) -> str:
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

    retry = 0
    best_result = None
    best_distance = float('inf')
    target = (min_length_no_space + max_length_no_space) / 2

    while retry < max_retry:
        try:
            resp = client.chat.completions.create(
                model=Model.GPT4_1,
                messages=[
                    {"role": "system", "content": "You are a professional blog post writer. Your task is to generate a blog post based on provided analysis data and user instructions."},
                    {"role": "user", "content": prompt}
                ],
                # max_completion_tokens=2200
            )
            text = resp.choices[0].message.content.strip()
            n = length_no_space(text)
            print(f"[시도 {retry+1}] 공백 제외 길이: {n}")

            if is_len_between(text, min_length_no_space, max_length_no_space, inclusive=True):
                print("✅ 조건 충족 — 문서 생성 완료")
                return text

            
            dist = abs(target - n)
            if dist < best_distance:
                best_distance = dist
                best_result = text

            print(f"⚠ 길이 {min_length_no_space}~{max_length_no_space} 범위 밖 — 재시도")
            retry += 1

        except Exception as e:
            print(f"OpenAI API 호출 오류: {e}")
            retry += 1

    print("⚠ 최대 재시도 도달 — 가장 근접한 문서 반환")
    return best_result or ""