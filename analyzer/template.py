from openai import OpenAI
import json
from config import OPENAI_API_KEY
from typing import Dict, List
from openai.types.chat import ChatCompletion

def generate_template_from_segment(
    text_segment: str,
    known_parameters_map: Dict[str, List[str]]
) -> str:
    """
    주어진 텍스트 세그먼트(문장/문단)에서 known_parameters_map에 있는 값들을 해당 대표 키워드로 대체하여 템플릿을 생성합니다.
    OpenAI API를 사용하여 문맥을 고려한 대체 작업을 수행합니다.

    Args:
        text_segment (str): 원본 텍스트 세그먼트
        known_parameters_map (Dict[str, List[str]]): '대표 키워드': ['값1', '값2', ...] 형태의 매핑

    Returns:
        str: 파라미터 대체가 적용된 템플릿 텍스트
    """
    if not OPENAI_API_KEY:
        raise ValueError("API 키가 설정되지 않았습니다. .env 파일에 OPENAI_API_KEY를 추가해주세요.")

    client: OpenAI = OpenAI(api_key=OPENAI_API_KEY)

    # known_parameters_map을 AI가 이해하기 쉬운 문자열 형태로 변환
    param_list_str: str = json.dumps(known_parameters_map, ensure_ascii=False, indent=2)

    prompt: str = f"""
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
        response: ChatCompletion = client.chat.completions.create(
            model="gpt-5-mini-2025-08-07",
            messages=[
                {"role": "system", "content": "You are a text templating assistant. Your task is to replace specific values in a given text segment with their corresponding category placeholders based on a provided parameter map. Output only the templated text."},
                {"role": "user", "content": prompt}
            ],
        )
        content: str | None = response.choices[0].message.content
        templated_text: str = content.strip() if content else ""
        return templated_text

    except Exception:
        return ''
