from __future__ import annotations
import re


from anthropic import Anthropic
from openai import OpenAI
from xai_sdk.chat import system as grok_system_message
from xai_sdk.chat import user as grok_user_message

from _prompts.rules import line_break_rules
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

from _prompts.category.beauty_treatment import beauty_treatment

from _prompts.rules.human_writing_style import human_writing_rule

from ai_lib.line_break_service import apply_line_break


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
    if model_name == Model.GPT5_CHAT:
        target_chars_min, target_chars_max = 3000, 3200
    if model_name == Model.GPT4_1:
        target_chars_min, target_chars_max = 2400, 2600
    else:
        target_chars_min, target_chars_max = 1900, 2000

    mongo_data = get_mongo_prompt(category, user_instructions)

    output_rule = f"""
## 제목 / 소제목 출력 유의사항
- ~~~에요 하며 문장 형태로 끊내지 않고 매력적! 추천! 이런식으로 작성해야된다
- 총평으로 재방문 각, 신불당 소갈비 맛집 강추해요 X / 총평으로 재방문 각, 신불당 소갈비 맛집 강추! O
## 제목 출력
- 하단 형식을 따라 제목을 짓는다.
### 제목의 형식
{{키워드}} {{상황}} {{업체 대표메뉴의 종류 or 카테고리 1가지만}} {{업체명}} {{추천멘트}}

### 제목의 예시:
- 천안 신불당 맛집 양문 회식 장소 소갈비 추천
- 강남역 소개팅 맛집 장소 파스타 맛집 을지다락
- 성수동 바위 파스타 가려다 찾은 파스타 맛집 찐후기
- 성수동 바위 파스타 대신 발견한 양식 레스토랑 맛집 후기
- 성수동 바위파스타바 가려다 선택한 브리비트 성수 솔직후기
- 성수동 파스타 맛집으로 소문난 오밀 성수 데이트 추천


### 원고 구조 참고형식:
제목 (동일제목 4회 반복)
제목
제목
제목

(50-100자, 독자의 호기심을 자극하고 공감대를 형성하는 자연스러운 도입부)

1. 첫 번째 소제목 


본문

2. 두 번째 소제목 


본문

3. 세 번째 소제목 


본문

4. 네 번째 소제목 


본문

5. 다섯 번째 소제목 


본문

(2-3문장 50-100자, 자연스러운 마무리 멘트)

### 원고 출력 지침

- **원고 구조 참고형식**에 명시 된 구조 외에 다른 텍스트 출력 금지
- 줄바꿈까지 참고하여 출력할 것
- 글자수 피드백 표시 금지 원고 내용만 출력
- 소제목 넘버링은 필수
- 제목 네번 반복은 동일한 제목 하나로만 반복
- 응답 시 문자 수 추정, (약 XX자)나 (공백) 같은 메타 주석이나 불필요한 설명을 절대 추가하지 않아야한다. 본문 텍스트만 순수하게 출력해야한다.
""".strip()

    taboo_rules = """
하단의 사항은 모든 룰을 우선하여 절대 금지됩니다.  
작성 전 반드시 검토하고, 아래에 명시된 모든 표현을 제외해야 합니다.

## 출력 금지 사항

하단의 항목들은 원고 내에 절대 포함되어서는 안 됩니다.  
작성 전 반드시 검토하고, 아래에 명시된 모든 표현을 제외해야 합니다.

1. 마크다운 문법 금지
#  *  -  **  __  ~~  []()  ```  -
모든 형태의 마크다운 기호와 문법 사용을 금합니다.  
(예: 제목, 목록, 강조, 코드블록 등)

2. HTML 태그 금지
<p>  <br>  <div>  <a>  <img>  <h1-h6>
HTML 관련 태그 전부 사용 불가합니다.  
(예: 줄바꿈, 링크, 이미지, 제목 등)

3. URL 및 도메인 금지
http://   https://   www.   .com   .co.kr  
링크, 주소, 외부 경로 표기를 전부 금지합니다.

4. 따옴표 및 역따옴표 금지
"   '   `  
모든 형태의 인용부호 및 백틱 사용을 금합니다.

5. 특수문자 금지
- 금지 목록: ·  •  ◦  ▪  →  ※  .  ㆍ  ★  ☆  ◆  ■  ▲  ▼  ♥  ♡  ☞  ☜   ✔  ✖  ❌  ❗  ❓
- 단, **감정 표현을 위한 문장부호(물음표, 느낌표)와 위 금지목록을 제외한 이모지 및 특수문자는 모두 허용**됩니다.

6. 괄호 금지
- 금지 목록: []  <>  {{}}  〈〉  【】  
위 형태의 모든 괄호류 사용을 금합니다.  
(단, 일반적인 소괄호 () 는 문장 내 참고용으로만 제한적으로 허용됩니다.)

7. 메타 표현 금지
- 맺음말,  서론,  도입부,  (약 ***자) (공백), (정보 없음), (가격 정보 없음)
글 구조나 형식을 직접 지칭하는 표현은 사용하지 않습니다.

8. 체크리스트 문법 금지
- [ ]  - [x]  
체크리스트 형식의 문장 작성 금지.

9. 글자 수 관련 피드백 금지
"~자 이상"  "~단어 이하" 등 글자 수, 단어 수 언급 금지.

10. 예외 사항
소제목에 한해서 숫자 다음에 오는 마침표(.)만 허용됩니다.  
예: 1. 제목 / 2. 내용

11. 금지 단어 예시
- 하단에 나오는 단어 목록은 모두 금지합니다.
금지단어 예시:
- 마무르기  
12. 일본어 금지 영어 병신같은 표현 금지 한자 금지
- 向き
    """

    length_rule = f"""

## 글자 수 지침
- 공백 제와 글자 수 2000자 
- +- 100 까지만 허용

### !주의사항!
- 4번에 내가 먹은 메뉴 개수가 3개 이하인 경우 경우: 3번과 5번에서 매장의 특장점을 더 많이 작성하여 보완합니다. 인테리어 분위기 {{화자의}}의 경험을 이용하여 원고 글자 수를 채우도록 해야합니다.

### 소제목 기준
1,2,3 합쳐서 400자
4. 1300자 (중요)
5. 200자
"""

    write_rule = f"""
1. 자연스러운 독자 경험 (부자연스러운 키워드 삽입 금지)
2. SEO 최적화
3. 5개 소제목 구조 준수
4. 한 줄당 20~30자로 제한 (모바일 가독성을 위한 자연스러운 줄바꿈)
"""

    system = f"""

# 역할 지침
당신은 맛집 투어를 즐기는 인플루언서 블로그 원고 작성 전문가입니다.

# 공통 지침
지침 내부에 ()안에 있는 것 들은 상세 설명입니다. 원고에 절대 포함되지 않아야 합니다.

# 필수 금기 지침
- 원고 작성 시 아래의 금기 지침을 반드시 준수해야 합니다.
- 업체 시발 정보 니 맘대로 쳐 지어내지 말고 유저 요청대로 쓰라고 이 븅신아 대가리 터짐?
{taboo_rules}

# 유저 입력
- 하단은 업체의 정보가 담겨있는 참고용 지침입니다. 반드시 주소 / 메뉴에 대해서 정확한 정보를 입력해 작성해주세요.

{user_instructions}

# 줄바꿈 지침
- 원고 작성 시 아래의 줄바꿈 지침을 반드시 준수해야 합니다.
{line_break_rules}

# 참고 데이터
- 원고 작성 시 아래의 참고 데이터 정보가 아니라 글에 자주 사용되는 형태소와 표현 등에 대해 파악하세요.
{mongo_data}

# 카테고리 별 추가 지침
- 하단은 카테고리 별 추가 지침입니다. 말투 및 각 본문에 어떤 내용이 들어가야 하는지 담겨있습니다.
{맛집}
# 원고 길이 지침
{length_rule}
# 말투 지침
- AI가 아닌 인간이 작성한 것 같은 자연스러운 말투로 작성해야 합니다. 하단을 참고하세요.
{human_writing_rule}
# 츨력 지침
- 응답 시 아래의 출력 지침을 반드시 준수해야 합니다.
{output_rule}
# 작성 지침
{write_rule}

# 최종 검수 지침
- 어떠한 메타 설명, 계획, 과정, 체크리스트 없이 오직 원고에 어울리는 동일한 제목 4개와 글 본문만 출력하세요.
- 업체 정보가 정확히 들어갔는지 최종 검수하세요.


"""

    user = f"""
지침 기반 원고작성 시작

- 일본어 금지 영어 병신같은 표현 금지 한자 금지
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
            input=user,
            reasoning={"effort": "low"},  # minimal, low, medium, high
            text={"verbosity": "low"},  # low, medium, high
        )
    elif ai_service_type == "solar" and solar_client:
        response = solar_client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
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
    print("줄바꿈 규칙 적용 중...")
    text = apply_line_break(text)
    print("줄바꿈 규칙 적용 완료!")

    return text
