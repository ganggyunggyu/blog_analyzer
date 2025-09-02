from __future__ import annotations
import re

from openai import OpenAI
from config import OPENAI_API_KEY
from _constants.Model import Model
from utils.query_parser import parse_query


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

    print(f"Chunk Service {user_instructions}")
    parsed = parse_query(user_instructions)

    if not parsed["keyword"]:
        raise ValueError("키워드가 없습니다.")

    keyword = parsed["keyword"]

    user: str = (
        f"""

[개요]
하단에 있는 참조원고 한줄한줄 전부 꼼꼼히 쪼갠 후에 어투나 이음세만 살짝 바꿔서 완전히 유사한 모양새의 원고로 다시 줘
이렇게 하면 글씨 길이도 당연히 참조 원고랑 비슷해야하고 그 안에 있는 표현같은것도 전부 비슷하겠지?

핵심 키워드를 파악해서 그런 것들의 개수도 유사해야해

그리고 스토리텔링 같은 것만 살짝 변화하는거야
예를 들어 4명이 간다 그러면 3명
20대 여성이다 그러면 30대 여성 이런 식으로

그리고 표현도 에시를 몇개 줄게 참고해 
예시는 참고만 하고 모든걸 그대로 사용하지말고 창의적으로 글을 만들어줘야해

[이행 사안]

{{}} << 이런 부분은 변수니까 항상 동일하지 않게 채워넣어줘
- 변수는 내가 준 것 말고도 상황에 따라 직접 만들어서 사용해야해
- 하단에 원본과 변환본은 단지 예시일 뿐이라 내가 준 것들 안에서만 활용해서는 안돼 언제나 유동적으로 직접 찾아서 변환해줘
- 변수는 원고에서는 티가 나서는 안돼 그냥 단어로 사용해줘 그냥 글인거야
- 원본/변환본의 유사도를 분석해서 마지막에 --- 하고 아래에 적어줘

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

[금지 사안]

이런 블로그 요소들은 따라하지않아도돼 -> {{재생
2

좋아요
0

00:28

접기/펴기}}, {{📍인천공항 택시 예약 바로가기📍

인천공항택시콜센터
인천공항 매일 운행 일반/대형/콜밴 배차 1666-8856 24시간 예약 상담

pf.kakao.com}}


    {keyword}
---
""".strip()
    )

    print(f"Chunk Service 파싱 결과: {parsed}")

    try:
        print(
            f"Chunk GPT 생성 시작 | keyword={user_instructions!r} | model={model_name}"
        )
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {
                    "role": "system",
                    "content": "너는 원고를 청크로 쪼개서 다시 만들어주는 전문가야",
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
            print(
                f"KKK Service tokens in={in_tokens}, out={out_tokens}, total={total_tokens}"
            )

        choices = getattr(response, "choices", []) or []
        if not choices or not getattr(choices[0], "message", None):
            raise RuntimeError("모델이 유효한 choices/message를 반환하지 않았습니다.")

        text: str = (choices[0].message.content or "").strip()
        if not text:
            raise RuntimeError("모델이 빈 응답을 반환했습니다.")

        length_no_space = len(re.sub(r"\s+", "", text))
        print(f"KKK {model_name} 문서 생성 완료 (공백 제외 길이: {length_no_space})")

        return text

    except Exception as e:
        print("KKK OpenAI 호출 실패:", repr(e))
        raise
