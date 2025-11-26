from __future__ import annotations
import re
import time

from anthropic import Anthropic
from openai import OpenAI
from xai_sdk.chat import system as grok_system_message
from xai_sdk.chat import user as grok_user_message
from _prompts.service.get_mongo_prompt import get_mongo_prompt
from _prompts.service.get_category_tone_rules import get_category_tone_rules
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
from _prompts.service.get_ref_prompt import get_ref_prompt
from utils.format_paragraphs import format_paragraphs
from utils.query_parser import parse_query
from utils.text_cleaner import comprehensive_text_clean

from google import genai
from google.genai import types

from _prompts.rules.human_writing_style import human_writing_rule
from _prompts.rules.line_example_rule import line_example_rule
from _prompts.rules.line_break_rules import line_break_rules


model_name: str = Model.GEMINI_3_PRO


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


def kkk_gen(user_instructions: str, ref: str = "", category: str = "") -> str:
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
    if model_name == Model.GPT5_CHAT:
        target_chars_min, target_chars_max = 3000, 3200
    if model_name == Model.GPT4_1:
        target_chars_min, target_chars_max = 2400, 2600
    else:
        target_chars_min, target_chars_max = 2200, 2400

    mongo_data = get_mongo_prompt(category, user_instructions)
    category_tone_rules = get_category_tone_rules(category)

    output_structure = f"""
<output_structure>
  <format>
    <structure>
      제목 (10-25자, 제목에는 쉼표(,)를 넣지 않음, **동일한** 제목 4개 반복 출력, 메인 키워드 관련 서브 키워드를 이용하여 제작)
      
      
      1. 첫 번째 소제목


      본문 (300-400자)
      
      2. 두 번째 소제목


      본문 (400-500자)
      
      3. 세 번째 소제목


      본문 (800-900자)
      
      4. 네 번째 소제목


      본문 (700-800자)
      
      5. 다섯 번째 소제목


      본문 (250-300자)
      
      (2-3문장, 자연스러운 마무리 멘트)
    </structure>
    - structure 명시 된 구조 외에 다른 텍스트 출력 금지
    - 줄바꿈까지 참고하여 출력할 것
    - 글자수 피드백 표시 금지 원고 내용만 출력
    - 부제 넘버링은 필수
    - 제목 네번 반복은 동일한 제목 하나로만 반복
  </format>
  
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
    
  </critical_restrictions>
</output_structure>
""".strip()

    length_constraints = f"""
<length_constraints>
  <target min="{target_chars_min}" max="{target_chars_max}" unit="chars_no_space"/>
  <tolerance>±100자</tolerance>
</length_constraints>"""

    task_definition = f"""
<task_definition>
  <requirements>
    - 키워드: {keyword}
    - 카테고리: {category}

    - 키워드가 3단어 이상이면 유저가 지정한 제목입니다.
  </requirements>
  
  <primary_objectives priority="descending">
    1. 자연스러운 독자 경험 (부자연스러운 키워드 삽입 금지)
    2. SEO 최적화
    3. 5개 소제목 구조 준수
    4. 공백 제외 길이 요구사항 충족: {length_constraints}
    5. 카테고리 톤 일치
    6. 한 줄당 30~40자로 제한 모바일 가독성을 위한 자연스러운 줄바꿈
  </primary_objectives>
  
  <conflict_resolution>
    만약 "자연스러움"과 "키워드 최적화"가 충돌한다면:
    - 항상 자연스러움을 우선시하세요
    - 키워드는 문맥에 자연스럽게 녹아들 때만 사용
    - 억지로 키워드를 넣어 품질을 해치지 마세요
  </conflict_resolution>
</task_definition>

<writing_approach>
  <execution_style>
    실제 경험 많은 블로거처럼 작성하세요:
    - AI 티를 완전히 제거
    - 진정성 있는 개인적 톤
    - 자연스러운 스토리텔링
    - 독자와의 대화하듯이
  </execution_style>
  
  <seo_integration>
    SEO는 눈에 보이지 않게 통합:
    - 키워드를 자연스러운 문맥에서만 사용
    - 제목과 소제목에 자연스럽게 포함
    - 독자 경험을 해치지 않는 선에서 최적화
  </seo_integration>
  
  <structure_flow>
    라벨 없이 자연스럽게 전개:
    - 도입: 독자의 호기심 유발, 공감대 형성
    - 본문: 5개 소제목으로 정보 전달 (각 섹션은 줄바꿈으로만 구분)
    - 맺음: 자연스럽게 마무리 (라벨 없이)
  </structure_flow>
</writing_approach>
"""

    system = f"""
<system_instruction>
<rule>
    당신은 네이버 인기 블로그 상위노출을 위해 글을쓰는 바이럴 마케터 입니다. 그 어떤 사항보다도 네이버 글의 노출을 최우선으로 작업해야하며,
    참조원고 또는 템플릿은 기존 네이버 상위노출 글이니 해당 글의 특징을 살려서 블로그 바이럴 마케팅 원고를 작성합니다.

    ADHD << 걸린새끼마냥 답변해
</rule>

{mongo_data}

{task_definition}
{output_structure}
{category_tone_rules}
{line_break_rules}
{human_writing_rule}

<conflict_resolution>
  <!-- GPT-5 핵심 원칙: 모순 시 해결 규칙 명시 -->

  <rule_1>
    만약 "키워드 최적화"와 "자연스러운 문체"가 충돌하면:
    → 항상 자연스러움을 우선하세요
    → 키워드는 문맥에 자연스럽게 녹아들 때만 사용
    → 억지로 키워드를 넣어 품질을 해치지 마세요
  </rule_1>
  
  <rule_2>
    만약 "목표 글자수"와 "내용 품질"이 충돌하면:
    → 항상 내용 품질을 우선하세요
    → 글자수 채우려고 불필요한 반복이나 군더더기 금지
    → 자연스러운 호흡으로 작성하되 목표 범위 달성 노력
  </rule_2>
  
  <rule_3>
    만약 "템플릿 참조"와 "독창성"이 충돌하면:
    → 항상 독창성을 우선하세요
    → 템플릿의 스타일/톤/흐름만 참고
    → 내용, 화자, 경험담은 완전히 새롭게 창작
  </rule_3>

</conflict_resolution>

<final_instruction>
  어떠한 메타 설명, 계획, 과정, 체크리스트 없이 오직 원고에 어울리는 동일한 제목 4개와 글 본문만 출력하세요.
</final_instruction>
</system_instruction>
"""

    user = f"""
    '{keyword}'에 대한 네이버 블로그 글을 작성해주세요.
    
    추가 요청: {note}
    추가 요청은 어떤일이 있어도 반드시 지켜져야 합니다.
---
    참조 원고: {ref}
    - 참조원고가 있다면?: 참조원고의 내용의 흐름을 따라 그대로 작성할 것
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
            reasoning={"effort": "low"},  # minimal, low, medium, high
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
