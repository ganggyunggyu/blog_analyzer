import re
from openai import OpenAI
import json
from config import OPENAI_API_KEY

def extract_expressions_with_ai(text: str) -> dict:
    if not OPENAI_API_KEY:
        raise ValueError("API 키가 설정되지 않았습니다. .env 파일에 OPENAI_API_KEY를 추가해주세요.")

    client = OpenAI(api_key=OPENAI_API_KEY)

    prompt = f"""
    다음은 블로그 원고의 일부입니다.

    [원고 내용]
    {text}

    [요청]
    위 원고 내용에서 마케팅/콘텐츠 제작에 유용하게 활용될 수 있는 '표현'들을 추출해주세요.
    '표현'은 특정 중분류(예: '긍정적 평가', '부정적 평가', '제품 특징', '서비스 장점', '사용 후기', '감성 표현', '행동 유도', '문제점 제시', '해결책 제시', '비교/대조', '수치/통계', '질문 유도')에 적합한 단어 또는 짧은 문장(구)입니다.
    각 표현은 해당 중분류의 '키'에 해당하는 '밸류'로 매칭시켜주세요.
    결과는 반드시 다음 JSON 형식으로 반환해주세요.

    {{
      "중분류_키1": ["표현1", "표현2"],
      "중분류_키2": ["표현3", "표현4"]
    }}
    """

    try:
        response = client.chat.completions.create(
            model='gpt-4.1-mini-2025-04-14',
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert in marketing content analysis. Your task is to extract useful expressions from the given text, categorize them into mid-level categories, and return them in a JSON format of 'category_key': ['expression1', 'expression2']."
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            
        )

        raw = response.choices[0].message.content.strip()
        cleaned = re.sub(r"^```json|```$", "", raw).strip()
        return json.loads(cleaned)

    except Exception as e:
        print(f"OpenAI API 호출 중 오류가 발생했습니다: {e}")
        return None