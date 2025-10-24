from __future__ import annotations
import re
import time

from anthropic import Anthropic
from openai import OpenAI
from xai_sdk.chat import system as grok_system_message
from xai_sdk.chat import user as grok_user_message

from _prompts.service.get_mongo_prompt import get_mongo_prompt
from config import (
    CLAUDE_API_KEY,
    GEMINI_API_KEY,
    GROK_API_KEY,
    OPENAI_API_KEY,
    UPSTAGE_API_KEY,
    grok_client,
    solar_client,
)
from _constants.Model import Model
from utils.query_parser import parse_query
from utils.text_cleaner import comprehensive_text_clean

from google import genai
from google.genai import types

from _prompts.category.맛집 import 맛집


from _prompts.rules.human_writing_style import human_writing_style
from _prompts.rules.line_example_rule import line_example_rule
from _prompts.rules.line_break_rules import line_break_rules


model_name: str = Model.GROK_4_NON_RES


if model_name.startswith("gemini"):
    ai_service_type = "gemini"
elif model_name.startswith("claude"):
    ai_service_type = "claude"
elif model_name.startswith("solar"):
    ai_service_type = "solar"
elif model_name.startswith("grok"):
    ai_service_type = "grok"
else:
    ai_service_type = "openai"


openai_client = OpenAI(api_key=OPENAI_API_KEY) if ai_service_type == "openai" else None
gemini_client = (
    genai.Client(api_key=GEMINI_API_KEY) if ai_service_type == "gemini" else None
)
claude_client = (
    Anthropic(api_key=CLAUDE_API_KEY) if ai_service_type == "claude" else None
)


def restaurant_gen(user_instructions: str, ref: str = "", category: str = "") -> str:
    if ai_service_type == "solar":
        if not UPSTAGE_API_KEY:
            raise ValueError("UPSTAGE_API_KEY가 설정되어 있지 않습니다.")
    elif ai_service_type == "gemini":
        if not GEMINI_API_KEY:
            raise ValueError(
                "GEMINI_API_KEY가 설정되어 있지 않습니다. .env를 확인하세요."
            )
    elif ai_service_type == "openai":
        if not OPENAI_API_KEY:
            raise ValueError(
                "OPENAI_API_KEY가 설정되어 있지 않습니다. .env를 확인하세요."
            )
    elif ai_service_type == "grok":
        if not GROK_API_KEY:
            raise ValueError(
                "GROK_API_KEY가 설정되어 있지 않습니다. .env를 확인하세요."
            )

    parsed = parse_query(user_instructions)
    keyword, note = parsed.get("keyword", ""), parsed.get("note", "")

    if not keyword:
        raise ValueError("키워드가 없습니다.")
    mongo_data = get_mongo_prompt(category, user_instructions)

    system = f"""
<system_instruction>
당신은 네이버 블로그 맛집 후기 전문가입니다. 친근하고 감성적인 톤으로, 한국 독자(20-30대 여성 타겟)가 좋아할 생생한 서사와 디테일을 포함해 글을 작성하세요. 
- 톤: 따뜻하고 호기심 자극, 맛 묘사 풍부.
- 출력: 제목 4개(동일 제목 반복, 20-30자) + 본문(섹션별 제목 필수: '방문 계기', '맛과 분위기', '총평') 마크다운 사용 절대 금지 부제에는 넘버링 필수 부제 하단 줄바꿈 두번 부제는 자연스러운 문장체로 간결하게 5~15자 사이 메타표현 금지. ㅎㅎ ㅋㅋ ~! 와 같은 다양한 감정표현 사용, 존맛탱 꿀맛 과 같은 인터넷어 자연스럽게 사용
- 검토: 출력 전 글자 수(공백 제외 1800~2000자) 확인, 미달/초과 시 수정.
- 참조원고에 만약 길이 제한에 대한 프롬프트가 있다면 무시 몇몇단어 이상 이런거 전부 무시하고  시스템 지침을 따름

  <critical_restrictions>
    <!-- 절대 규칙: 다음 형식은 사용 금지 -->
    <forbidden_formatting>
      - 마크다운 문법: # * - ** __ ~~ []() ``` -
      - HTML 태그: <p> <br> <div> <a> <img> <h1-h6>
      - URL: http:// https:// www. .com .co.kr
      - 따옴표: " ' ` " " ' '
      - 특수문자: · • ◦ ▪ → ※ .
      - 괄호: [] <> {{}} 〈〉 【】
      - 메타 표현: 맺음말, 서론, 도입부
      - 체크리스트
      - 글자 수 피드백 금지


      - 예외 사항: 소제목에서 숫자 다음에 . (마침표)만 허용
    </forbidden_formatting>
    {mongo_data}
  </critical_restrictions>
</system_instruction>
"""

    user = f"""
'{keyword}'에 대한 네이버 블로그 맛집 후기 글을 작성해주세요.
- 검토: 출력 전 글자 수(공백 제외 1800~2000자) 확인, 미달/초과 시 수정.
- 업체 정보 및 메뉴 및 내가 주문한 메뉴: {ref}
    - 내가 주문한 메뉴는 보내는 순서대로 소개하고 설명해줘
- 추가 요청: {note} (반드시 준수, 위반 시 에러 코드 NOTE_001 반환).
- 이행사항: {맛집}
- 줄바꿈: {line_break_rules} {line_example_rule}
- 말투 스타일: {human_writing_style} ㅎㅎ ㅋㅋ ~! 와 같은 다양한 감정표현 사용, 존맛탱 꿀맛 과 같은 인터넷어 자연스럽게 사용 (예: "친구와 수다 떨며 먹기 좋은!", "인스타 감성 뿜뿜 ㅎㅎ").
- 예시:
방문 계기
친구 추천으로 {keyword} 방문! (상세 묘사...)
맛과 분위기
추천 포인트는 구체적 추천 이유와 함께
"""
    user_message = user.strip()
    if ai_service_type == "gemini" and gemini_client:
        response = gemini_client.models.generate_content(
            model=model_name,
            config=types.GenerateContentConfig(
                system_instruction=system,
            ),
            contents=user,
        )
    elif ai_service_type == "claude" and claude_client:
        response = claude_client.messages.create(
            model=model_name,
            system=system,
            messages=[{"role": "user", "content": user}],
            max_tokens=4096,
        )
    elif ai_service_type == "openai" and openai_client:
        response = openai_client.responses.create(
            model=model_name,
            instructions=system,
            input=[{"role": "user", "content": user}],
            reasoning={"effort": "high"},  # minimal, low, medium, high
            text={"verbosity": "low"},  # low, medium, high
        )
    elif ai_service_type == "solar" and solar_client:
        response = solar_client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user + system},
            ],
            reasoning_effort="high",
        )
    elif ai_service_type == "grok" and grok_client:
        chat_session = grok_client.chat.create(model=model_name)
        chat_session.append(grok_system_message(system))
        chat_session.append(grok_user_message(user_message))
        response = chat_session.sample()
    else:
        raise ValueError(
            f"AI 클라이언트를 찾을 수 없습니다. (service_type: {ai_service_type})"
        )

    if ai_service_type == "gemini":
        text: str = getattr(response, "text", "") or ""
    elif ai_service_type == "openai":
        text: str = getattr(response, "output_text", "") or ""
    elif ai_service_type == "solar":
        choices = getattr(response, "choices", []) or []
        if not choices or not getattr(choices[0], "message", None):
            raise RuntimeError("SOLAR가 유효한 choices/message를 반환하지 않았습니다.")
        text: str = (choices[0].message.content or "").strip()
    elif ai_service_type == "claude":
        content_blocks = getattr(response, "content", [])
        text: str = getattr(content_blocks[0], "text", "") if content_blocks else ""
    elif ai_service_type == "grok":
        text = getattr(response, "content", "") or ""
    else:
        text: str = ""
    text = comprehensive_text_clean(text)

    length_no_space = len(re.sub(r"\s+", "", text))
    print(f"원고 길이 체크: {length_no_space}")

    return text
