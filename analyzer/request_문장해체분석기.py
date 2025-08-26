from openai import OpenAI
import os
from constants.Model import Model
from textwrap import dedent

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def get_문장해체(ref: str, model: str = Model.GPT4_1) -> str:

    if ref == "":
        return ""

    schema_block = dedent(
        """
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

        "부제 분석": {
    "설명": "위 원고의 중요 내용으로 부제를 분석한다. 부제는 5개로 제한한다.",
    다음 원고를 읽고, 글의 흐름과 핵심 주제를 기준으로 부제를 5개만 뽑아줘.
    주절주절 하지말고 깔끔 명료하게 작성해야합니다.
    지역역명이나 변경되어도 무방한 것들은 그대로 하지말고 유동적으로 변경해서 만들어야합니다.
    - 예: 수원 -> 동탄

    조건:
    - 반드시 5개
    - 짧고 간결하게 (한 줄, 10자 내외)
    - 글의 중요한 내용을 놓치지 말 것
    - 새로 창작하지 말고 원고 속 실제 의미와 흐름을 반영할 것
    - 업체명은 언급 금지 키워드 위주로 부제목 제작
        - 인천공항은 업체명이 아님
    - 부제 앞에는 번호 필요 
        1. 부제 1
        2. 부제 2
        ...
    - JSON 배열로 반환 (예: ["...", "...", "...", "...", "..."])
    
    }
    "원고 스타일 세부사항": [
        "문단 길이, 문체 특징, 반복 패턴, 리듬감 등 원고의 스타일적 특징을 Value List 형식으로 나열"
    ]
    }}
    """
    ).strip()

    system = (
        "You are an expert in text analysis and narrative style extraction. "
        "Your task is to analyze the given manuscript and output structured metadata. "
        "Return ONLY in JSON format, no explanations, no extra text."
    )

    user = f"""
    다음은 블로그 원고입니다.

    [원고]

    - 원고에 나오는 업체명은 언급 금지입니다.
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
        temperature=0,
    )
    out = resp.choices[0].message.content or ""
    return out.strip()
