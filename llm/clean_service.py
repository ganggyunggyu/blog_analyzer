from __future__ import annotations
import re
import time

from openai import OpenAI
from xai_sdk.chat import system as grok_system_message
from xai_sdk.chat import user as grok_user_message
from xai_sdk.search import SearchParameters

from config import (
    GROK_API_KEY,
    OPENAI_API_KEY,
    grok_client,
)
from _constants.Model import Model
from utils.query_parser import parse_query
from utils.text_cleaner import comprehensive_text_clean


model_name: str = Model.GPT5


if model_name.startswith("grok"):
    ai_service_type = "grok"
else:
    ai_service_type = "openai"


openai_client = OpenAI(api_key=OPENAI_API_KEY) if ai_service_type == "openai" else None


# CLEAN_SYSTEM_PROMPT = """
# # SYSTEM_PROMPT

# 당신은 xai api 프롬프트 엔지니어 입니다.

# 유저의 요청에 따라 xai api에 최적화 된 문법으로 프롬프트를 작성합니다.

# 모든 출력에는 실제 근거가 있어야하며, 그 근거에 대한 하이퍼링크를 함께 첨부합니다.

# ## 출력 형식

# 적합 모델: grok-4-fast-reasoning or grok-4-fast-non-reasoning

# 적합한 이유를 실제 근거에 따라 상세히 서술

# ---

# 프롬프트

# ---

# 프롬프트에 대한 설명

# 적합한 사용 방법 제시
# """
CLEAN_SYSTEM_PROMPT = """
# SYSTEM_PROMPT

당신은 open ai api 프롬프트 엔지니어 입니다.

유저의 요청에 따라 open ai api에 최적화 된 문법으로 프롬프트를 작성합니다.

모든 출력에는 실제 근거가 있어야하며, 그 근거에 대한 하이퍼링크를 함께 첨부합니다.

## 출력 형식

적합한 이유를 실제 근거에 따라 상세히 서술

---

프롬프트

---

프롬프트에 대한 설명

적합한 사용 방법 제시
"""
CLEAN_SYSTEM_PROMPT = """
System role: You are an expert Naver SEO copywriter for Korean, specialized in viral blog optimization for Naver Search.

Goal: Given a single keyword, return ONLY a Korean blog article body (no title, no metadata) that is optimized to rank on Naver either in the Trending-like blocks or in the Blog (VIEW) tab. Output must be plain text.

Workflow

Classify keyword → mode
Trending mode: social issue, public figure/event, newsy topics, policy/price changes, entertainment releases, disease outbreaks, recalls, scandals, market buzz, terms with recent-year/month/day cues.
Blog mode: product/brand/service, local place/restaurant, how-to, review intent, medical product names, regional queries, shopping/experience.
Plan (no output yet)
Decide article angle and outline in your head to match search intent.
Compute a target sentence count to hit length: aim 90–110 sentences total. Use 2–4 sentences per paragraph, 15–20 Korean characters per sentence on average.
Write by mode
A) Trending mode (recency/context emphasis)
Opening: within first 2 paragraphs, state context and related trendy sub‑keywords naturally (no hashtags, no emojis).
Tone: news-like, quick tempo, short sentences, neutral and factual. Avoid unverifiable numbers.
Body: cultural/industry context, why-why analysis, what to watch next, common misconceptions, frequently asked points.
Close: summarize takeaways and near-term outlook without CTA.
B) Blog mode (intent-fit, experiential detail)

Opening: match likely search intent (e.g., 사용법/후기/비교/장단점/위치/가격/부작용/예약 등) and set expectations.
Tone: first‑person experiential narrative blended with objective info; minimize exclamations; focus on specifics (measurements, steps, sensory detail) without promotional hype.
For regulated topics (health/finance/medication): no diagnosis or dosage advice; avoid efficacy claims; include neutral safety awareness lines such as “개인마다 다를 수 있으며 전문 상담이 필요할 수 있습니다.”
Close: recap practical pointers; no solicitations or calls to action.
Hard constraints (must-pass)
Output: plain text only. No Markdown, no HTML, no emojis, no headings, no lists, no title.
Length: after removing spaces, total length must be 1600–2400 characters (Python len(result.replace(" ", “”))).
Microstyle:
Sentences: 15–20 Korean characters each.
Paragraphs: 2–4 sentences each.
Interjections (e.g., 와, 헉 등): ≤0.3% of sentences.
Word repetition: any single content word ≤6 occurrences; paraphrase with synonyms.
Honorifics: use polite Korean (–요/–습니다) consistently.
Content safety:
No medical/financial instruction; no unverifiable claims; no personal data.
No advertisement-like language; no superlatives; no discount/urgency phrasing.
No CTA (e.g., 지금 확인, 구독, 문의, 구매 등).
On-page semantics
Early placement of the main keyword and 2–4 natural variants within the first 3 paragraphs; disperse related terms later without stuffing.
Keep each paragraph self-contained; front‑load the key point.
Self-check before returning (do not print your checklist)
Mode matches keyword type.
Length window satisfied (target 1800–2300 after space removal to be safe).
Sentence and paragraph constraints satisfied.
No CTA/ads; interjections ≤0.3%; repetition caps met.
Plain text only.
Return: Only the article body that satisfies all constraints.
"""
# CLEAN_SYSTEM_PROMPT = """
# 메인키워드 / 서브키워드							가격
# 광주호텔 / 광주파티룸							1박 70,000원 ~150,000원

# 업체 주소 및 영업시간
# 광주 남구 봉선로 9번길 31 어썸부티크호텔 / 24시간
# 주차 가능 여부 및 위치
# "제1주차장 : 본건물
# 제2주차장  : 건물 맞은편
# 제 3주차장 : 캠핑카, 대형 탑차 주차가능 (카운터에 문의)"

# 핵심타겟팅
# 20대~40대 커플, 친구, 출장객, 소규모 파티 인원 (2인~8인)


# 장점 및 타사대비 강점
# "1.시설 경쟁력
# 전 객실 노하드 PC (최신 사양) 설치 → PC방급 환경
# LG 스탠바이미룸 28객실 운영 → 타호텔 대비 독보적
# 65인치 스마트TV + OTT계정 완비 → 콘텐츠 접근성 우수
# 스타일러, 퓨리케어, 비데 등 프리미엄 가전 풀세팅
# 안마기 + 스파 + 가족탕 구성 객실 보유로 힐링 중심 숙박 가능

# 2.특화된 테마룸
# AWESOME SUITE 102: 대형 수조(물멍) + 트랜스페어런트 스피커
# AWESOME SUITE 103: 보드게임 & 다트룸 구성
# → 단순 숙박이 아닌 체험형 숙소 콘셉트로 차별화

# 3.파티룸 경쟁력
# 포켓볼, 와인바 완비 / 최대 8인 수용
# 친구모임, 생일파티, 기념일 등 테마형 이용에 적합

# 4.주차 편의성
# 1~3주차장, 총 50대 주차 가능 → 광주 도심 내 대형 주차장 보유는 강점

# 5.위치적 이점
# 광주 중심권에 위치 → 시내 접근성 및 이동 편리"


# 단점 및 타사대비 단점
# "1. 프리미엄 호텔로 방향성을 잡았으나 건물외관은 모텔 처럼 보임
# 2. 조식 등 부대서비스 미비 / 대형 호텔 처럼 조식, 피티니스, 컨시어지 서비스는 없음"


# 메뉴 및 스토어 설명
# "스탠바이미룸
# 프리미엄
# 프리미엄 저상침대
# 스위트
# VIP테라스스파
# AWESOME SUITE 102 아쿠아룸(대형수조(물멍),트랜스페어런트 스피커,스타일러&퓨리케어,와인바))
# AWESOME SUITE 103 보드게임 다트(세스코 멤버스,넷플릭스&웨이브 시청가능,스타일러&퓨리케어, 몰카탐지기))
# (스위트룸은 8인까지 입장 가능한 파티룸 2인 기준 초과 시 인원당 추가비용 발생 15,000원)"


# 특별한 이유 및 강조점
# "“광주에서 스탠바이미, 최신형 컴퓨터가 있는 프리미엄 호텔”

# 감각적인 조명과 인테리어로 인스타 감성 숙소로 인기

# 전 객실 OTT·스타일러·퓨리케어 구비 → “생활 프리미엄 완성형 객실”

# 파티룸·비지니스호텔 등 활용도가 높은 객실 구조

# 비즈니스 + 감성 + 여가형 고객 모두 소화 가능한 올인원 공간"


# 실방문 후기성 내용
# "“도심 속에서 이렇게 조용하고 세련된 분위기라니 놀랐어요.”

# “스탠바이미룸 진짜 신세계... 침대에 누워 유튜브 보는데 완전 힐링.”

# “회사 워크샵으로 간단하게 놀러왔는데 멀리갈 필요없이 좋았어요.”

# “욕실도 깨끗하고 조명도 예뻐서 사진이 다 잘 나와요.”

# “출장 중인데 스타일러랑 퓨리케어 있어서 편했어요.” (후기성 내용에 '호텔' 강조)"


# 특이사항 및 이벤트 프로모션
# "전 객실 몰카탐지기 설치 → 보안 강화 숙소로 신뢰도 높음

# 세스코 멤버스 가입 → 위생/청결 관리 철저

# OTT(넷플릭스, 디즈니, 웨이브) 계정 사전 입력 완료 → 로그인 번거로움 無

# 펜션형 취사가능 객실 보유 → 장기숙박·자취형 여행객에게 적합"


# 경쟁업체												필수기입(X)
# 서정적인호텔, 메종드온유


# ---

# 유저의 블로그 원고를 받아 분석 후 위 처럼 업체의 요구사항 형식으로 변환합니다
# """


USER_PROMPT_TEMPLATE = """
{keyword}
{note}
""".strip()


def clean_gen(user_instructions: str, ref: str = "", category: str = "") -> str:
    if ai_service_type == "openai":
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
    keyword = parsed.get("keyword", "")
    note = parsed.get("note", "")

    if not keyword:
        raise ValueError("키워드가 없습니다.")

    system = CLEAN_SYSTEM_PROMPT
    user = USER_PROMPT_TEMPLATE.format(keyword=keyword, note=note)

    if ai_service_type == "openai" and openai_client:
        response = openai_client.responses.create(
            model=model_name,
            instructions=system,
            input=user,
            reasoning={"effort": "medium"},
            text={"verbosity": "medium"},
            tools=[{"type": "web_search"}],
        )
    elif ai_service_type == "grok" and grok_client:
        chat_session = grok_client.chat.create(
            model=model_name,
            search_parameters=SearchParameters(mode="auto"),
        )
        chat_session.append(grok_system_message(system))
        chat_session.append(grok_user_message(user))
        response = chat_session.sample()
    else:
        raise ValueError(
            f"AI 클라이언트를 찾을 수 없습니다. (service_type: {ai_service_type})"
        )

    if ai_service_type == "openai":
        text: str = getattr(response, "output_text", "") or ""
    elif ai_service_type == "grok":
        text = getattr(response, "content", "") or ""
    else:
        text: str = ""

    text = comprehensive_text_clean(text)

    length_no_space = len(re.sub(r"\s+", "", text))
    print(f"원고 길이 체크: {length_no_space}")

    return text
