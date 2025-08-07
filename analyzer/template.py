import re
from openai import OpenAI
import json
from config import OPENAI_API_KEY

def generate_template_from_segment(text_segment: str, known_parameters_map: dict) -> str:
    """
    주어진 텍스트 세그먼트(문장/문단)에서 known_parameters_map에 있는 값들을 해당 대표 키워드로 대체하여 템플릿을 생성합니다.
    OpenAI API를 사용하여 문맥을 고려한 대체 작업을 수행합니다.
    """
    if not OPENAI_API_KEY:
        raise ValueError("API 키가 설정되지 않았습니다. .env 파일에 OPENAI_API_KEY를 추가해주세요.")

    client = OpenAI(api_key=OPENAI_API_KEY)

    # known_parameters_map을 AI가 이해하기 쉬운 문자열 형태로 변환
    param_list_str = json.dumps(known_parameters_map, ensure_ascii=False, indent=2)

    prompt = f"""
    다음은 원본 텍스트의 한 부분과, 이 텍스트 내에서 대체될 수 있는 파라미터들의 목록입니다.
    파라미터 목록은 '대표 키워드': ['값1', '값2'] 형태의 JSON 객체입니다.

    [원본 텍스트 세그먼트]
    {text_segment}

    [파라미터 목록]
    {param_list_str}

    [요청]
    원본 텍스트 세그먼트 내에서 '파라미터 목록'에 있는 '값'들을 찾아서 해당 '대표 키워드'로 대체해주세요.
    예를 들어, '갤럭시S24'라는 값이 '제품명'이라는 대표 키워드에 속한다면, 원본 텍스트의 '갤럭시S24'를 '[제품명]'으로 대체해야 합니다.
    대체된 결과만 출력해주세요. 다른 설명이나 추가적인 텍스트는 포함하지 마세요.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini-2025-04-14", # 또는 gpt-3.5-turbo
            messages=[
                {"role": "system", "content": "You are a text templating assistant. Your task is to replace specific values in a given text segment with their corresponding category placeholders based on a provided parameter map. Output only the templated text."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1, # 창의성보다는 정확한 대체에 초점
            max_tokens=500 # 세그먼트 단위이므로 토큰 제한을 더 낮게 설정
        )
        templated_text = response.choices[0].message.content.strip()
        return templated_text

    except Exception as e:
        print(f"OpenAI API 호출 중 오류가 발생했습니다: {e}")
        return None