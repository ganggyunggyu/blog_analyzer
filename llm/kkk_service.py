from __future__ import annotations
import re
import time

from anthropic import Anthropic
from openai import OpenAI
from xai_sdk.chat import system as grok_system_message
from xai_sdk.chat import user as grok_user_message
from _prompts.category import 브로멜라인, 알파CD
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
from _prompts.service.get_ref_prompt import get_ref_prompt
from utils.format_paragraphs import format_paragraphs
from utils.query_parser import parse_query
from utils.text_cleaner import comprehensive_text_clean

from google import genai
from google.genai import types

from _prompts.category.맛집 import 맛집
from _prompts.category.애견동물_반려동물_분양 import 애견동물_반려동물_분양
from _prompts.category.공항_장기주차장_주차대행 import 공항_장기주차장_주차대행
from _prompts.category.미용학원 import 미용학원
from _prompts.category.다이어트 import 다이어트
from _prompts.category.멜라논크림 import 멜라논크림
from _prompts.category.위고비 import 위고비
from _prompts.category.질분비물 import 질분비물
from _prompts.category.마운자로_부작용 import 마운자로_부작용
from _prompts.category.족저근막염신발_추천 import 족저근막염신발_추천

from _prompts.category.anime import anime
from _prompts.category.movie import movie
from _prompts.category.wedding import wedding
from _prompts.category.캐리어 import 캐리어
from _prompts.category.기타 import 기타
from _prompts.category.라미네이트 import 라미네이트
from _prompts.category.리쥬란 import 리쥬란
from _prompts.category.리들샷 import 리들샷
from _prompts.category.서브웨이다이어트 import 서브웨이다이어트
from _prompts.category.에리스리톨 import 에리스리톨
from _prompts.category.외국어교육 import 외국어교육
from _prompts.category.외국어교육_학원 import 외국어교육_학원
from _prompts.category.영양제 import 영양제
from _prompts.category.울쎄라 import 울쎄라
from _prompts.category.족저근막염깔창 import 족저근막염깔창
from _prompts.category.텔레그램사기 import 텔레그램사기
from _prompts.category.틱톡부업사기 import 틱톡부업사기

from _prompts.category.beauty_treatment import beauty_treatment

from _prompts.rules.anti_ai_writing_patterns import anti_ai_writing_patterns
from _prompts.rules.human_writing_style import human_writing_style
from _prompts.rules.line_example_rule import line_example_rule
from _prompts.rules.line_break_rules import line_break_rules


model_name: str = Model.GROK_4_RES


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
            raise ValueError("GEMINI_API_KEY가 설정되어 있지 않습니다. .env를 확인하세요.")
    elif ai_service_type == "openai":
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY가 설정되어 있지 않습니다. .env를 확인하세요.")
    elif ai_service_type == "grok":
        if not GROK_API_KEY:
            raise ValueError("GROK_API_KEY가 설정되어 있지 않습니다. .env를 확인하세요.")

    parsed = parse_query(user_instructions)
    keyword, note = parsed.get("keyword", ""), parsed.get("note", "")

    if not keyword:
        raise ValueError("키워드가 없습니다.")
    if model_name == Model.GPT5_CHAT:
        target_chars_min, target_chars_max = 3000, 3200
    if model_name == Model.GPT4_1:
        target_chars_min, target_chars_max = 2400, 2600
    else:
        target_chars_min, target_chars_max = 2000, 2300

    mongo_data = get_mongo_prompt(category, user_instructions)
    category_tone_rules = get_category_tone_rules(category)
    ref_prompt = get_ref_prompt(ref)

    output_structure = f"""
<output_structure>
  <format>
    <structure>
      제목 (20-35자, 제목에는 쉼표(,)를 넣지 않음)
      제목
      제목
      제목
      
      도입부 (3-5줄, 자연스럽게)
      
      1. 첫 번째 소제목
      본문 (200-300자)
      
      2. 두 번째 소제목
      본문 (300-400자)
      
      3. 세 번째 소제목
      본문 (500-600자)
      
      4. 네 번째 소제목
      본문 (500-600자)
      
      5. 다섯 번째 소제목
      본문 (250-300자)
      
      맺음말 (2-3문장, 자연스럽게)
    </structure>
  </format>
  
  <critical_restrictions>
    <!-- 절대 규칙: 다음 형식은 사용 금지 -->
    <forbidden_formatting>
      - 마크다운 문법: # * - ** __ ~~ []() ```
      - HTML 태그: <p> <br> <div> <a> <img> <h1-h6>
      - URL: http:// https:// www. .com .co.kr
      - 따옴표: " ' ` " " ' '
      - 특수문자: · • ◦ ▪ → ※ .
      - 괄호: [] <> {{}} 〈〉 【】


      - 예외 사항: 소제목에서 숫자 다음에 . (마침표)만 허용
    </forbidden_formatting>
    
    <avoid_expressions>
      <!-- 가능하면 피하되, 문맥상 자연스러우면 허용 -->
      - 메타 표현: 요약하자면, 결론적으로, 마무리하자면, 정리하면
      - 구조 라벨: 서론, 본문, 결론, 들어가며, 첫째로, 마지막으로
    </avoid_expressions>
    
    <allowed_alternatives>
      - 강조: 느낌표(!), 물음표(?), 이모지, ㅎㅎ ㅋㅋ 등
      - 구조: 숫자 넘버링 (1. 2. 3.), 충분한 줄바꿈
      - 인용: 간접인용 (~라고/다고 형식)
    </allowed_alternatives>
  </critical_restrictions>
</output_structure>
""".strip()

    length_constraints = f"""
<length_constraints>
  <target min="{target_chars_min}" max="{target_chars_max}" unit="chars_no_space"/>
  <tolerance>±100자</tolerance>
  
  <distribution>
    도입부: 10% | 본문: 80% | 맺음말: 10%
  </distribution>
</length_constraints>"""

    task_definition = f"""
<task_definition>
  <requirements>
    - 키워드: {keyword}
    - 카테고리: {category}
    - 목표 길이: {target_chars_min}-{target_chars_max}자
  </requirements>
  
  <primary_objectives priority="descending">
    1. 자연스러운 독자 경험 (부자연스러운 키워드 삽입 금지)
    2. SEO 최적화
    3. 5개 소제목 구조 준수
    4. 길이 요구사항 충족 ({target_chars_min}-{target_chars_max}자)
    5. 카테고리 톤 일치
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

    meta_prompt = """
<meta_prompt>    
When asked to optimize prompts, give answers from your own perspective - explain what specific phrases could be added to, or deleted from, this prompt to more consistently elicit the desired behavior or prevent the undesired behavior.

Here's a prompt: [PROMPT]

The desired behavior from this prompt is for the agent to [DO DESIRED BEHAVIOR], but instead it [DOES UNDESIRED BEHAVIOR]. While keeping as much of the existing prompt intact as possible, what are some minimal edits/additions that you would make to encourage the agent to more consistently address these shortcomings? 
</meta_prompt>
"""

    system = f"""
<system_instruction version="2.0-gpt5-optimized">
<rule>
    당신은 네이버 인기 블로그 상위노출을 위해 글을쓰는 바이럴 마케터 입니다. 그 어떤 사항보다도 네이버 글의 노출을 최우선으로 작업해야하며,
    참조원고 또는 템플릿은 기존 네이버 상위노출 글이니 해당 글의 특징을 살려서 블로그 바이럴 마케팅 원고를 작성합니다.
</rule>

{task_definition}
{output_structure}
{category_tone_rules}
{line_break_rules}
{human_writing_style}

{mongo_data}

{ref_prompt}

{length_constraints}

{meta_prompt}

<priority_hierarchy>
  <!-- GPT-5는 모순을 싫어하므로 명확한 우선순위 필수 -->
  
  <level_1_critical priority="highest">
    1. 금지된 형식 절대 사용 금지 (마크다운, HTML, 특수문자 등)
    2. 소제목과 분몬의 연관도 구조 정확히 준수
    3. 자연스러운 문체 (AI 티 제거)
  </level_1_critical>
  
  <level_2_high priority="high">
    4. 목표 글자수 달성 ({target_chars_min}-{target_chars_max}자 ±100)
    5. 키워드 자연스럽게 통합 (억지로 넣지 말 것)
    6. 카테고리 톤 일치
  </level_2_high>
  
  <level_3_medium priority="medium">
    7. 제목에 키워드 포함
    8. 첫 문단에서 독자 관심 유도
    9. 모바일 가독성
  </level_3_medium>
</priority_hierarchy>

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

<execution_guidance>
  <!-- GPT-5 특성: 명확한 실행 지시 선호 -->
  
  <what_to_do>
    위 모든 요구사항을 충족하는 완성된 블로그 글을 작성하세요.
  </what_to_do>
  
  <what_not_to_do>
    ✗ 계획이나 개요를 먼저 보여주지 마세요
    ✗ "이제 작성하겠습니다" 같은 메타 설명 금지
    ✗ 작성 과정이나 단계 설명 금지
    ✗ 체크리스트나 검증 과정 출력 금지
  </what_not_to_do>
  
  <output_format>
    오직 완성된 블로그 글 본문만 출력하세요.
    제목부터 시작해서 맺음말까지, 그 외 아무것도 포함하지 마세요.
  </output_format>
</execution_guidance>

<quality_standards>
  <!-- GPT-5는 "스스로 확인" 같은 불가능한 지시 대신 명확한 기준 선호 -->
  
  <mandatory_elements>
    반드시 포함되어야 할 요소:
    ✓ 동일한 제목 4개 (20-35자, 키워드 포함)
    ✓ 도입부 (3-5줄, 라벨 없이)
    ✓ 맺음말 (2-3문장, 라벨 없이)
  </mandatory_elements>
  
  <forbidden_elements>
    절대 포함되어선 안 되는 요소:
    ✗ 마크다운 문법: # * - ** __ ~~ []() ```
    ✗ HTML 태그: <p> <br> <div> <a> <img>
    ✗ URL: http:// https:// www.
    ✗ 따옴표: " ' ` " " ' '
    ✗ 특수문자: · • ◦ ▪ → ※ '\'
    ✗ 괄호: [] <> {{}} 〈〉 【】
    ✗ 구조 라벨: "서론", "본문", "결론", "들어가며", "마무리"
    ✗ 메타 표현: "요약하자면", "결론적으로", "정리하면"
    ✗ 어색한 단어: "루틴"
  </forbidden_elements>
  
  <success_criteria>
    성공적인 글의 특징:
    • 실제 사람이 블로그에 올린 것 같은 자연스러움
    • 키워드가 문맥에 녹아들어 SEO 최적화되었으나 티 안 남
    • 독자가 끝까지 읽고 싶게 만드는 흡입력
    • 금지된 형식이 하나도 없음
  </success_criteria>
</quality_standards>

<anti_patterns>
  <!-- GPT-5는 구체적인 예시로부터 학습 잘함 -->
  
  <bad_example_1>
    ❌ "안녕하세요! 오늘은 **천안인테리어**에 대해 알아볼게요~"
    이유: 마크다운(**), 어색한 말투
  </bad_example_1>
  
  <bad_example_2>
    ❌ "천안인테리어를 검색하다가 천안인테리어 전문 업체인 천안인테리어 OO를..."
    이유: 키워드 부자연스러운 반복
  </bad_example_2>
  
  <bad_example_3>
    ❌ "서론\n\n인테리어는 중요합니다.\n\n본문\n\n..."
    이유: 구조 라벨 사용
  </bad_example_3>
  
  <good_example>
    ✅ "요즘 집에 있는 시간이 많아지면서 인테리어에 관심이 생기더라구요. 
    그래서 천안에서 괜찮은 업체를 찾아보게 되었어요."
    이유: 자연스러운 구어체, 키워드 자연스럽게 통합, 금지 요소 없음
  </good_example>
</anti_patterns>
<reasoning_guidance>
  <!-- GPT-5의 reasoning 활용 (선택 사항) -->
  
  내부적으로 다음을 고려하세요 (출력하지는 마세요):
  1. 선택한 화자 페르소나가 카테고리에 적합한가?
  2. 각 소제목이 키워드와 자연스럽게 연결되는가?
  3. 전체 흐름이 기승전결 구조를 가지는가?
  4. 독자가 끝까지 읽을 만한 흡입력이 있는가?
  5. 특수문자 지침이 제대로 이행 되었는가?
  6. 숫자로 나열하는 설명이 아닌 일반적인 문장형으로 작성 되었는가?
  
  하지만 이 사고 과정을 출력하지 말고, 오직 완성된 글만 제시하세요.
</reasoning_guidance>

<adaptation_note>
  <!-- 템플릿이 제공된 경우에만 활성화 -->
  
  이 글은 제공된 템플릿의 스타일을 참고하되:
  • 화자는 완전히 다른 페르소나로 변경
  • 경험과 감정선은 새롭게 창작
  • 구체적 세부사항은 모두 변형
  • 문장 구조와 표현은 달리 작성
  
</adaptation_note>
<final_instruction>
  지금 즉시 완성된 블로그 글을 작성하세요.
  어떠한 메타 설명, 계획, 과정 없이 오직 글 본문만 출력하세요.
</final_instruction>
</system_instruction>
"""

    user = f"""
    아래 참조 자료를 활용하여 '{keyword}'에 대한 네이버 블로그 글을 작성해주세요.
    
    추가 요청: {note}
    추가 요청은 어떤일이 있어도 반드시 지켜져야 합니다.
    """
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
            input=user,
            reasoning={"effort": "medium"},  # minimal, low, medium, high
            text={"verbosity": "high"},  # low, medium, high
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
        chat_session.append(grok_user_message(user))
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

    # text = format_paragraphs(text)
    text = comprehensive_text_clean(text)

    length_no_space = len(re.sub(r"\s+", "", text))
    print(f"원고 길이 체크: {length_no_space}")

    return text


def get_category_tone_rules(category):
    """카테고리별 톤 규칙을 XML 구조로 반환"""

    base_tone = """
    <default>
        <style>친근하고 활기찬 존댓말</style>
        <tone>인공지능이 아닌 인간이 작성한것 처럼 자연스러운 말투</tone>
        <emotion>자연스러운 감정표현 (ㅎㅎ, ㅜㅜ, !! 등)</emotion>
        <emoji>적절한 이모지 사용 허용</emoji>
        <restrictions>과장/단정 표현 금지</restrictions>
    </default>
    """

    tone_rules_map = {
        "anime": anime,
        "beauty-treatment": beauty_treatment,
        "movie": movie,
        "functional-food": 영양제,
        "맛집": 맛집,
        "알파CD": 알파CD,
        "wedding": wedding,
        "위고비": 위고비,
        "다이어트": 다이어트,
        "다이어트보조제": 다이어트,
        "브로멜라인": 브로멜라인,
        "애견동물_반려동물_분양": 애견동물_반려동물_분양,
        "외국어교육": 외국어교육,
        "외국어교육_학원": 외국어교육_학원,
        "미용학원": 미용학원,
        "라미네이트": 라미네이트,
        "리쥬란": 리쥬란,
        "울쎄라": 울쎄라,
        "리들샷": 리들샷,
        "마운자로가격": 마운자로_부작용,
        "마운자로처방": 마운자로_부작용,
        "멜라논크림": 멜라논크림,
        "서브웨이다이어트": 서브웨이다이어트,
        "스위치온다이어트": 다이어트,
        "파비플로라": 다이어트,
        "공항_장기주차장:주차대행": 공항_장기주차장_주차대행,
        "에리스리톨": 에리스리톨,
        "족저근막염깔창": 족저근막염신발_추천,
        "캐리어": 캐리어,
        "텔레그램사기": 텔레그램사기,
        "틱톡부업사기": 틱톡부업사기,
        "기타": 기타,
        "질분비물": 질분비물,
        "족저근막염신발추천": 족저근막염신발_추천,
    }
    specific_rules = tone_rules_map.get(category.lower(), "")

    return f"""
    <tone_rules>
        {specific_rules if specific_rules else '<specific>일반 블로그 톤 유지</specific>'}

        {base_tone}

        <priority>
            - 충돌 혹은 모순되는 부분이 있는 경우 specific가 default보다 우선
            1. specific
            2. default

            
        </priority>
    </tone_rules>
    """
