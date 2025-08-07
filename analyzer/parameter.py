import os
from openai import OpenAI
import json
from config import OPENAI_API_KEY

def extract_and_group_entities_with_ai(full_text):
    """OpenAI API를 사용하여 원고 내용에서 직접 개체를 인식하고 그룹화합니다."""
    if not OPENAI_API_KEY:
        raise ValueError("API 키가 설정되지 않았습니다. .env 파일에 OPENAI_API_KEY를 추가해주세요.")

    client = OpenAI(api_key=OPENAI_API_KEY)

    prompt = f"""다음은 여러 블로그 원고를 합친 텍스트입니다.

[원고 내용]
{full_text}

[요청]
위 원고 내용에서 반복적으로 나타나거나, 대체 가능한 핵심 개체(entity)들을 모두 추출해주세요.
추출된 개체들을 의미적으로 유사한 항목끼리 그룹화하고, 각 그룹을 대표할 수 있는 가장 적절한 "대표 키워드"를 한 단어로 지정해주세요.
예를 들어, '땀땀', '토끼정'은 '상호명'으로, '갤럭시S24', '아이폰16'은 '제품명'으로 그룹화할 수 있습니다.
결과는 반드시 다음 JSON 형식으로 반환해주세요.

{{
  "대표 키워드1": ["추출된 개체1", "추출된 개체2"],
  "대표 키워드2": ["추출된 개체3", "추출된 개체4"]
}}
"""

    try:
        response = client.chat.completions.create(
            model='gpt-4.1-mini-2025-04-14',
            messages=[
                {"role": "system", "content": "You are an expert in Named Entity Recognition and text analysis. Your task is to extract key entities from the text and group them semantically into a JSON format."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        grouped_params = json.loads(response.choices[0].message.content)
        return grouped_params

    except Exception as e:
        print(f"OpenAI API 호출 중 오류가 발생했습니다: {e}")
        return None
