from openai import OpenAI
import os
from constants.Model import Model
from textwrap import dedent

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_문장해체(ref: str, model: str = Model.GPT5_MINI) -> str:

    schema_block = dedent("""
    {{
    "화자 지시": {{
        "키워드": "원고 주제 혹은 핵심 인물명",
        "화자": "화자의 연령/성별/특징",
        "말투": "주요 말투 및 억양, 사용되는 화법",
        "자주 등장한 단어": {{"__note": "단어:횟수 형태의 객체를 반환"}},
        "자주 등장한 형태소": ["자주 등장하는 표현들을 나열"]
    }},
    "구성 지시": {{
        "서론": "원고의 도입부 주제 요약",
        "중론": "중간 전개 요약",
        "결론": "마무리 및 귀결 요약"
    }},
    "원고 스타일 세부사항": [
        "문단 길이, 문체 특징, 반복 패턴, 리듬감 등 원고의 스타일적 특징을 Value List 형식으로 나열"
    ]
    }}
    """).strip()
        
    system = (
        "You are an expert in text analysis and narrative style extraction. "
        "Your task is to analyze the given manuscript and output structured metadata. "
        "Return ONLY in JSON format, no explanations, no extra text."
    )

    user = f"""
    다음은 블로그 원고입니다.

    [원고]
    {ref}

    [요청]
    아래 항목을 원고 내용에 맞게 추출해 JSON 형식으로만 반환하세요.

    하단에서 개수를 세는 부분은 정확하게 세어야합니다.

    {schema_block}

    반드시 위 JSON 형식만 출력하세요.

    """.strip()

    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    out = resp.choices[0].message.content or ""
    return out.strip()