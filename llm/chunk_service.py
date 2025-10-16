from __future__ import annotations
import re

from openai import OpenAI
from xai_sdk.chat import system as grok_system_message
from xai_sdk.chat import user as grok_user_message
from config import OPENAI_API_KEY, GROK_API_KEY, grok_client
from _constants.Model import Model
from utils.format_paragraphs import format_paragraphs
from utils.query_parser import parse_query
from utils.text_cleaner import clean_text_format


model_name: str = Model.GROK_4_RES

if model_name.startswith("grok"):
    ai_service_type = "grok"
else:
    ai_service_type = "openai"

openai_client = OpenAI(api_key=OPENAI_API_KEY) if ai_service_type == "openai" else None


def chunk_gen(user_instructions: str, ref: str = "", category: str = "") -> str:
    """
    Returns:
        생성된 원고 텍스트 (str)

    Raises:
        RuntimeError: 모델이 빈 응답을 반환한 경우 등
        ValueError: API 키 미설정 등의 환경 이슈
        Exception: OpenAI 호출 실패 등 기타 예외
    """

    if ai_service_type == "grok":
        if not GROK_API_KEY:
            raise ValueError(
                "GROK_API_KEY가 설정되어 있지 않습니다. .env를 확인하세요."
            )
    elif ai_service_type == "openai":
        if not OPENAI_API_KEY:
            raise ValueError(
                "OPENAI_API_KEY가 설정되어 있지 않습니다. .env를 확인하세요."
            )

    print(f"Chunk Service {user_instructions}")
    parsed = parse_query(user_instructions)

    if not parsed["keyword"]:
        raise ValueError("키워드가 없습니다.")

    keyword = parsed["keyword"]

    system = """
너는 원고를 청크로 쪼개 재구성하는 전문가야. 참조 원고를 한 줄씩 꼼꼼히 분석한 후, 어투·연결어만 살짝 바꿔 유사한 구조의 새 원고로 만들어줘. 이렇게 하면 길이·표현이 원본과 비슷해질 거야!

[개요]
참조 원고를 쪼개서 재배치: 글자 수(공백 제외) 95% 일치, 키워드 빈도(예: "주차대행" 5회 → 비슷하게) 유지. 이모지·표현(~~, ㅎㅎ, !! 등) 그대로 쓰되, 비슷한 톤의 다른 이모지로 살짝 변형 필수(예: ✅ → ✔️). 스토리만 유연 변형(4인 여행 → 3인, 20대 여성 → 30대 남성, 고등학생 과정 → 성인 워크숍). 교육 관련은 실무 카테고리(예: 마케팅 세미나)로 변경. 부제는 의미 유지+약간 수정(예: "주차 팁" → "주차 꿀팁"). 업체명 언급 금지: "제가 이용한 업체"나 "이 서비스 업체"로 치환. 작성자가 있는 경우 윤우 로 치환.

변수: {{}}는 맥락 따라 새로 채워(예: {{A}} → "김"씨). 자연스럽게 녹여내. 출력 끝에 --- 후 "원본 vs 변환: 키워드 95% 일치, 구조 90%, 전체 유사도 70% (변형으로 낮춤)" 분석 추가. 유사도 과다 피하기 위해 흐름·단어 유지하면서 재배치—code_execution으로 검증 추천.
[문단정리 지침]
- 한 줄당 30~40자로 제한 모바일 가독성을 위한 자연스러운 줄바꿈

[이행 예시] (참고만, 창의적으로 변형)
- 원본: 오메가3 하루섭취량과 복용시간은? (알티지, 초임계, 고순도)
  - 변환: 오메가3 매일 섭취량 팁과 타이밍? (알티지, 초임계, 고순도) ㅎㅎ
- 원본: 안심하고 먹을 수 있겠더라고요.
  - 변환: 마음 놓고 챙겨볼 수 있겠다는 기분이 들더라!!
- 원본: 오메가3 하루섭취량 기준과 복용시간
  - 변환: 오메가3 섭취량 기준점 그리고 복용 시기
- 원본: ㄱ씨
  - 변환: 박씨
- 원본: 저는 집이 남양주라 인천공항 콜택시 가격이
  - 변환: 우리 집이 수원이라 인천공항 콜택시 요금이
- 원본: 새벽 출국이나 늦은 입국에도
  - 변환: 이른 새벽 비행이나 늦은 밤 귀국 때도

[금지 사안]
길이 그대로: 확장·축소 NO. 블로그 UI(좋아요 수, 배너 등) 무시. 키워드: 쉼표 없이(위고비 알약 O, 위고비, 알약 X). 유사도 <80%로 유지—검색 기반 창의성 더해.
"""

    user: str = (
        f"""
    [참조원고]

    {ref}

    [키워드]

    {keyword}
---
""".strip()
    )

    print(f"Chunk Service 파싱 결과: {parsed}")

    try:
        print(f"Chunk 생성 시작 | keyword={user_instructions!r} | model={model_name}")

        if ai_service_type == "grok" and grok_client:
            chat_session = grok_client.chat.create(model=model_name)
            chat_session.append(grok_system_message(system))
            chat_session.append(grok_user_message(user.strip()))
            response = chat_session.sample()
        elif ai_service_type == "openai" and openai_client:
            response = openai_client.chat.completions.create(
                model=model_name,
                messages=[
                    {
                        "role": "system",
                        "content": system,
                    },
                    {
                        "role": "user",
                        "content": user,
                    },
                ],
            )
        else:
            raise ValueError(
                f"AI 클라이언트를 찾을 수 없습니다. (service_type: {ai_service_type})"
            )

        if ai_service_type == "grok":
            text: str = getattr(response, "content", "") or ""
        elif ai_service_type == "openai":
            usage = getattr(response, "usage", None)
            if usage is not None:
                in_tokens = getattr(usage, "prompt_tokens", None)
                out_tokens = getattr(usage, "completion_tokens", None)
                total_tokens = getattr(usage, "total_tokens", None)
                print(
                    f"Chunk Service tokens in={in_tokens}, out={out_tokens}, total={total_tokens}"
                )

            choices = getattr(response, "choices", []) or []
            if not choices or not getattr(choices[0], "message", None):
                raise RuntimeError(
                    "모델이 유효한 choices/message를 반환하지 않았습니다."
                )

            text: str = (choices[0].message.content or "").strip()
        else:
            text: str = ""

        if not text:
            raise RuntimeError("모델이 빈 응답을 반환했습니다.")

        length_no_space = len(re.sub(r"\s+", "", text))
        print(f"Chunk {model_name} 문서 생성 완료 (공백 제외 길이: {length_no_space})")

        text = clean_text_format(text)

        return text

    except Exception as e:
        print(f"Chunk {ai_service_type} 호출 실패:", repr(e))
        raise
