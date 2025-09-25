from __future__ import annotations
from datetime import datetime
from typing import List, Dict, Any
import time
import json


from openai import OpenAI
from config import OPENAI_API_KEY
from _constants.Model import Model
from mongodb_service import MongoDBService


model_name: str = Model.GPT5
client = OpenAI(api_key=OPENAI_API_KEY)


def template_gen(
    user_instructions: str, docs: str, category: str, file_name: str = ""
) -> str:
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY가 설정되어 있지 않습니다. .env를 확인하세요.")

    db_service = MongoDBService()
    db_service.set_db_name(category)

    # 파일명 중복 체크 (파일명이 있는 경우에만) - AI 요청 전에 체크!
    if file_name.strip():
        existing_template = db_service.find_documents(
            "templates", {"file_name": file_name.strip()}
        )
        if existing_template:
            print(f"이미 처리된 파일입니다: {file_name}")
            print("기존 템플릿을 반환합니다. (AI 요청 없음 - 비용 절약!)")
            db_service.close_connection()
            return existing_template[0].get("templated_text", "")

    print(f"새로운 파일 처리 시작: {file_name or '파일명 없음'}")

    analysis_data: Dict[str, Any] = db_service.get_latest_analysis_data() or {}

    expressions_raw = analysis_data.get("expressions") or {}
    parameters_raw = analysis_data.get("parameters") or {}

    expressions: Dict[str, List[str]] = {
        str(k): [str(vv).strip() for vv in (v or []) if str(vv).strip()]
        for k, v in expressions_raw.items()
    }
    parameters: Dict[str, List[str]] = {
        str(k): [str(vv).strip() for vv in (v or []) if str(vv).strip()]
        for k, v in parameters_raw.items()
    }

    expressions_json = json.dumps(expressions, ensure_ascii=False)
    parameters_json = json.dumps(parameters, ensure_ascii=False)

    system = """
You are a text templating assistant. Your task is to replace specific values in a given text segment with their corresponding category placeholders based on a provided parameter map. Output only the templated text.
""".strip()

    prompt = f"""

[요청]
- 원본 텍스트 세그먼트 내에서 '파라미터 목록'에 있는 VALUE들을 찾아서 해당 KEY로 대체해주세요.
- 예를 들어, '갤럭시S24'라는 값이 '제품명'이라는 KEY에 속한다면, 원본 텍스트의 '갤럭시S24'를 '[제품명]'으로 대체해야 합니다.
- 예를 들어, '일론 머스크' or '빠니보틀' 등의 값이 '인물명'이라는 KEY에 속한다면, 원본 텍스트의 '일론 머스크'를 '[인물명]'으로 대체해야 합니다.

- 위 예 말고도 당신이 판단할때 변수로 사용할수 있다고 판단되는 부분은 모두 VALUE -> KEY로 치환합니다.
- 대체된 결과만 출력해주세요. 다른 설명이나 추가적인 텍스트는 포함하지 마세요.

---

[치환 예시]

- VALUE -> [KEY]

- "갤럭시S24" → [제품명]
- "아이폰16" → [제품명]
- "맥북 에어 M3" → [제품명]
- "에어팟 맥스" → [제품명]
- "플스5" → [제품명]

- "일론 머스크" → [인물명]
- "빠니보틀" → [인물명]
- "유재석" → [인물명]
- "아이유" → [인물명]
- "마이클 조던" → [인물명]

- "토끼정" → [상호명]
- "땀땀" → [상호명]
- "스타벅스" → [상호명]
- "쿠팡" → [상호명]
- "무신사" → [상호명]

- "세마글루타이드" → [성분]
- "오메가3" → [성분]
- "비타민D" → [성분]
- "콜라겐 펩타이드" → [성분]
- "히알루론산" → [성분]

- "메스꺼움" → [부작용]
- "어지럼증" → [부작용]
- "두통" → [증상]
- "복부 팽만감" → [증상]
- "피로감" → [증상]

- "15만원" → [가격]
- "29,900원" → [가격]
- "3개월" → [기간]
- "12kg 감량" → [수치]
- "혈압 160" → [수치]

- "효과가 좋았다" → [긍정평가]
- "가성비 최고" → [긍정평가]
- "만족도가 높다" → [긍정평가]
- "추천할 만하다" → [긍정평가]
- "디자인이 예쁘다" → [긍정평가]

- "부작용이 심하다" → [부정평가]
- "효과가 없었다" → [부정평가]
- "가격이 너무 비싸다" → [부정평가]
- "재구매 의사 없음" → [부정평가]
- "서비스가 불친절하다" → [부정평가]

***예시는 참고만! 실제 값은 표현 라이브러리와 파라미터를 필수 참고***
---


다음은 원고 원문의 한 부분과, 이 텍스트 내에서 대체될 수 있는 [파라미터 목록]과 [표현 라이브러리] 목록입니다.
파라미터 목록은 KEY: ['VALUE', 'VALUE' ...] 형태의 JSON 객체입니다.

[원고 원문]
<<<DOCS_BEGIN
{docs}
DOCS_END>>>

[파라미터 목록 (parameters) JSON]

## 파라미터 목록 데이터에 대한 가이드
    - 파라미터 데이터는 하단 내용대로 만들어졌으니 참고해서 사용
    위 원고 내용에서 반복적으로 나타나거나, 대체 가능한 핵심 개체(entity)들을 모두 추출해주세요.
    추출된 개체들을 의미적으로 유사한 항목끼리 그룹화하고, 각 그룹을 대표할 수 있는 가장 적절한 "대표 키워드"를 한 단어로 지정해주세요.
    예: '땀땀', '토끼정' → '상호명',  '갤럭시S24', '아이폰16' → '제품명'

    반드시 아래 JSON 형식으로만 반환하세요(문자 이외 설명 금지).
    {{
    "대표 키워드1": ["추출된 개체1", "추출된 개체2"],
    "대표 키워드2": ["추출된 개체3", "추출된 개체4"]
    }}

<<<PARAM_BEGIN
{parameters_json}
PARAM_END>>>

[표현 라이브러리 (expressions) JSON]

## 표현 라이브러리에 대한 가이드
    - 표현 라이브러리 데이터는 하단 내용대로 만들어졌으니 참고해서 사용

    위 원고 내용에서 마케팅/콘텐츠 제작에 유용하게 활용될 수 있는 '표현'들을 추출해주세요.
    '표현'은 특정 중분류(예: '긍정적 평가', '부정적 평가', '제품 특징', '서비스 장점', '사용 후기', '감성 표현', '행동 유도', '문제점 제시', '해결책 제시', '비교/대조', '수치/통계', '질문 유도')에 적합한 단어 또는 짧은 문장(구)입니다.
    각 표현은 해당 중분류의 '키'에 해당하는 '밸류'로 매칭시켜주세요.
    결과는 반드시 다음 JSON 형식으로 반환해주세요.
    문맥에 맞게 expressions JSON의 키워드를 직접 KEY([긍정적 표현], [부정적 표현], 등) 형태로 끼워 넣으세요.
    ### 사용 가능한 키 목록
    {_KEY_LIST}
    **이 외에도 유동적으로 추가 가능**

    출력 예시:
    {{
      "중분류_키1": ["표현1", "표현2"],
      "중분류_키2": ["표현3", "표현4"]
    }}

    {{
    "긍정적 평가": ["만족도가 높다", "추천할 만하다"],
    "부정적 평가": ["아쉬운 점", "가격 부담"]
    }}

    ### 예시
    - [부정적 표현]: [사실은 꺼려졌어요​, 이해 불가능이었어요​]
    - [긍정적 표현]: [매우 깨끗하게 보관이 되었어요​, 믿을 수 있는곳]
    - [행동 유도]: [하는 경우에는 참고해 보세요​]

<<<EXP_BEGIN
{expressions_json}
EXP_END>>>


{user_instructions}
""".strip()
    start_ts = time.time()

    res = get_openai(model=model_name, user=prompt, system=system)

    text = get_openai_text(res)

    now = datetime.utcnow()
    doc = {
        "timestamp": now,
        "file_name": file_name,
        "category": category,
        "templated_text": text,
    }

    # 템플릿 저장 (위에서 중복 체크 완료했으므로 안전하게 저장)
    template_id = "저장 실패"
    try:
        result = db_service.insert_document("templates", doc)
        template_id = str(result.inserted_id) if hasattr(result, 'inserted_id') else "저장 완료"
        print(f"템플릿 저장 완료: {file_name or '파일명 없음'}")
    except Exception as e:
        print(f"템플릿 저장 중 오류 (계속 진행): {e}")

    # 템플릿 정보와 함께 출력
    print(f"템플릿 [START] {file_name or '파일명 없음'}:{template_id}")
    print(f"템플릿 길이: {len(text)}자")
    print(text)

    elapsed = time.time() - start_ts
    if elapsed >= 60:
        minutes = int(elapsed // 60)
        seconds = int(elapsed % 60)
        print(f"{category}-템플릿 생성 소요시간: {minutes}분 {seconds}초")
    else:
        print(f"{category}-템플릿 생성 소요시간: {elapsed:.2f}초")

    db_service.close_connection()

    return text


def get_openai(model, user, system):
    return client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )


def get_openai_text(res):
    return res.choices[0].message.content or "".strip()


def get_minute(start_ts):
    elapsed = time.time() - start_ts


_KEY_LIST = [
    "긍정적 평가",
    "부정적 평가",
    "제품 특징",
    "서비스 장점",
    "사용 후기",
    "감성 표현",
    "행동 유도",
    "문제점 제시",
    "해결책 제시",
    "비교/대조",
    "수치/통계",
    "질문 유도",
    "가격/비용 언급",
    "효과/결과 강조",
    "부작용/리스크",
    "전문성/권위 언급",
    "브랜드/상호명 언급",
    "비유/상징 표현",
    "트렌드/인기",
]
