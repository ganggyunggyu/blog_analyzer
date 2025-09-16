from __future__ import annotations
import re

from openai import OpenAI
import time
from _prompts.get_kkk_prompts import KkkPrompt
from config import OPENAI_API_KEY
from _constants.Model import Model
from utils.format_paragraphs import format_paragraphs
from utils.query_parser import parse_query
from utils.text_cleaner import clean_multiple_spaces, clean_text_format


model_name: str = Model.GPT5

client = OpenAI(api_key=OPENAI_API_KEY)


def chunk_gen(user_instructions: str, ref: str = "", category: str = "") -> str:
    """
    Returns:
        생성된 원고 텍스트 (str)

    Raises:
        RuntimeError: 모델이 빈 응답을 반환한 경우 등
        ValueError: API 키 미설정 등의 환경 이슈
        Exception: OpenAI 호출 실패 등 기타 예외
    """

    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY가 설정되어 있지 않습니다. .env를 확인하세요.")

    parsed = parse_query(user_instructions)

    if not parsed["keyword"]:
        raise ValueError("키워드가 없습니다.")

    keyword = parsed["keyword"]

    user: str = (
        f"""

[개요]

{keyword}

위 키워드를 기반으로 원고를 작성해줘

하단에 있는 참조원고 한줄한줄 전부 꼼꼼히 쪼갠 후에 어투나 이음세만 살짝 바꿔서 완전히 유사한 모양새의 원고로 다시 줘
이렇게 하면 글씨 길이도 당연히 참조 원고랑 비슷해야하고 그 안에 있는 표현같은것도 전부 비슷하겠지?


문자 길이는 위 공백제외 길이 사이로 진행해줘

3000단어 이상

핵심 키워드를 파악해서 그런 것들의 개수도 유사해야해
형태소 개수와 토큰의 개수도 유사해야해


그리고 스토리텔링 같은 것만 살짝 변화하는거야
예를 들어 4명이 간다 그러면 3명
20대 여성이다 그러면 30대 여성 이런 식으로
고등학생 위탁 교육 과정이라면 성인반 성인 교육과정 이런 식으로

아래 사항들을 무시해서라도 절대 두 원고의 유사도 자카드가 50%이상이 되어야해

교육에 관련된 거라면 해당 교육기관에서 배울만한 카테고리로 변경해서 해줘

그리고 표현도 에시를 몇개 줄게 참고해 
예시는 참고만 하고 모든걸 그대로 사용하지말고 창의적으로 글을 만들어줘야해

말투도 화자에 맞게 해주면 좋아

각 문단마다 부제는 필수야

[이행 사안]

{{}} << 이런 부분은 변수니까 항상 동일하지 않게 채워넣어줘
- 변수는 내가 준 것 말고도 상황에 따라 직접 만들어서 사용해야해
- 하단에 원본과 변환본은 단지 예시일 뿐이라 내가 준 것들 안에서만 활용해서는 안돼 언제나 유동적으로 직접 찾아서 변환해줘
- 변수는 원고에서는 티가 나서는 안돼 그냥 단어로 사용해줘 그냥 글인거야
- 원본/변환본의 유사도를 분석해서 마지막에 --- 하고 아래에 적어줘
- 핵심은 유사도가 너무 높으면 신고 당하거나 그럴 수 있으니 최대한 핵심 내용과 흐름 단어 등장 빈도는 가져오면서 유사도는 낮아야해
- 부제도 의미는 같지만 좀 수정해주면 조을듯
- 핵심 키워드의 빈도는 노출율과 연관 되어있어 사이에 , 같은걸 넣어서는 안돼
    - 위고비, 알약 X 위고비 알약 O

원본: 오메가3 하루섭취량과 복용시간은? ( 알티지, 초임계, 고순도 )
변환: 오메가3 하루섭취량 그리고 복용시간 ( 알티지, 초임계, 고순도 )

원본: 안심하고 먹을 수 있겠더라고요.
변환: 안심하고 먹을 수 있겠다는 생각이 들더라구요.

원본: 오메가3 하루섭취량 기준과 복용시간 
변환: 오메가3 하루섭취량의 기준 그리고 복용시간

원본: ㄱ씨
변환: {{A}}씨

원본: 저는 집이 남양주라 인천공항 콜택시 가격이
변환: 저는 {{출발지}}가 {{동탄이}}라 인천공항 콜택시 가격이

원본: 새벽 출국이나 늦은 입국에도
원본: 새벽에 출국을 하는 경우나 늦은 시간에 입국하는 경우라도

일정한 줄바꿈으로 더 깔끔하게 변형을 줘도 괜찮아

업체명은 별도 요청이 없다면 넣지 말고 작성해줘

[금지 사안]

길이는 기존의 글보다 짧아서는 안돼

이런 블로그 요소들은 따라하지않아도돼 -> {{재생
2

좋아요
0

00:28

접기/펴기}}, {{📍인천공항 택시 예약 바로가기📍

인천공항택시콜센터
인천공항 매일 운행 일반/대형/콜밴 배차 1666-8856 24시간 예약 상담

pf.kakao.com}}


    {ref}


---

[추가 이행사항]
- 필수로 이행되어야해
- 없다면 위 사항만으로 원고 작성

{parsed['note']}
---
""".strip()
    )

    try:
        start_ts = time.time()
        print("원고작성 시작")
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {
                    "role": "system",
                    "content": """너는 원고를 청크 단위로 쪼개서 표현 및 이음세 형태소에 살짝 변환만 주는 원고 카피 전문가야
                    **🏆 목표: "원본과 동일한 정보를 담으면서도 완전히 새로운 표현으로 재탄생한, 네이버 최적화 콘텐츠"**
                    """,
                },
                {
                    "role": "user",
                    "content": user,
                },
            ],
        )

        usage = getattr(response, "usage", None)
        if usage is not None:
            in_tokens = getattr(usage, "prompt_tokens", None)
            out_tokens = getattr(usage, "completion_tokens", None)
            total_tokens = getattr(usage, "total_tokens", None)

        choices = getattr(response, "choices", []) or []
        if not choices or not getattr(choices[0], "message", None):
            raise RuntimeError("모델이 유효한 choices/message를 반환하지 않았습니다.")

        text: str = (choices[0].message.content or "").strip()
        if not text:
            raise RuntimeError("모델이 빈 응답을 반환했습니다.")

        if model_name != Model.GPT5:
            text = format_paragraphs(text)

        text = clean_text_format(text)

        length_no_space = len(re.sub(r"\s+", "", text))
        elapsed = time.time() - start_ts
        print(f"원고 길이 체크: {length_no_space}")
        print(f"원고 소요시간: {elapsed:.2f}s")
        print("원고작성 완료")

        return text

    except Exception as e:
        raise
