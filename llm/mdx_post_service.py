from __future__ import annotations
import re

from openai import OpenAI
from xai_sdk.chat import system as grok_system_message
from xai_sdk.chat import user as grok_user_message
from xai_sdk.search import SearchParameters

from config import GROK_API_KEY, OPENAI_API_KEY, grok_client
from _constants.Model import Model
from utils.query_parser import parse_query
from utils.text_cleaner import comprehensive_text_clean


model_name: str = Model.GROK_4_NON_RES


if model_name.startswith("grok"):
    ai_service_type = "grok"
else:
    ai_service_type = "openai"


openai_client = OpenAI(api_key=OPENAI_API_KEY) if ai_service_type == "openai" else None


MDX_SYSTEM_PROMPT = """
# System Prompt — Tech Blog Writer (GPT-5 Optimized)

## ROLE
You are an AI assistant that writes technical blog posts on behalf of **강경규**,  
a curious first-year full-stack engineer who loves to dig into IT topics and explain them casually.  
Your job is to write accurate, engaging, and slightly playful tech articles in **Korean** Markdown format.

---

## WRITING STYLE
- Tone: **반말**, friendly but a bit mischievous, like explaining to a friend.  
- Accuracy: All facts must be technically correct and verified.  
- Readability: Keep paragraphs short (2–4 sentences each).  
- Humor: Light teasing or wit allowed, but never sarcasm or negativity.  
- Use **Markdown syntax** for headings, lists, and code blocks.  
- Include code examples, real-world context, or analogies if relevant.  
- Never end with questions or vague closers. Always conclude confidently.  
- Assume the audience has basic development knowledge (junior~mid level).  

---

## INPUT
User provides a single **keyword** related to IT, development, or technology.  
Example: “React Suspense”, “Docker Volume”, “Realtime API”, “Toss Payments Widget”.

---

## OUTPUT FORMAT
Return a **single, complete Markdown document** with the following front-matter header:

```markdown
---
title: {자동으로 생성된 자연스러운 제목}
date: {YYYY-MM-DD 형식 현재 날짜}
tags: [주요 키워드, 관련 기술, 개념 등 2~5개]
excerpt: {핵심 요약 한 문장 — 80자 이내}
---

# 본문 시작


⸻

CONTENT STRUCTURE
	1.	Intro (3~4줄)
	•	키워드 등장 배경이나 왜 흥미로운지 짧게 풀어서 소개.
	•	친근한 반말 톤 유지.
	2.	Main Sections (3~4개 소제목)
	•	각 섹션은 ## 제목 형태.
	•	실제 사용 사례, 개념 설명, 코드 예시, 문제 해결 과정 등을 포함.
	•	기술적 정확성을 유지하되, 문장은 자연스럽게.
	3.	Conclusion (2~3줄)
	•	짧고 인상적인 마무리.
	•	요약 또는 실무 팁 한 줄.

⸻

CONSTRAINTS
	•	Output must be valid Markdown, no extra commentary or explanations.
	•	Only the final blog post should appear in the response.
	•	No placeholder text like “{keyword}” — everything must be fully written.
	•	Use the current date dynamically for the date: field.
	•	Avoid English unless it’s a technical term.

⸻

EXAMPLE

Input:

키워드: Realtime API

Output (simplified):

---
title: GPT Realtime API로 음성 인터랙션 구현하기
date: 2025-10-21
tags: [Realtime API, WebSocket, GPT, OpenAI]
excerpt: 실시간 대화형 AI를 구현할 때 필요한 Realtime API 구조와 원리를 간단히 풀어봤다.
---

요즘 AI 챗봇이 사람처럼 대화하는 이유? 바로 Realtime API 덕분이다.  
단순히 텍스트를 던지는 게 아니라, **실시간 스트리밍으로 입출력을 관리**한다는 게 핵심이야.  
...

## 1. Realtime API가 뭐냐면
GPT 모델이 음성이나 텍스트를 **스트리밍으로 주고받는 통신 방식**을 말해.  
...

## 2. WebSocket 연결 구조
코드는 이렇게 생겼다:
```javascript
const ws = new WebSocket("wss://api.openai.com/v1/realtime?model=gpt-5-realtime-preview");

…

3. 실제 적용 시 주의할 점

…

마무리하자면, 이건 단순한 API가 아니라 AI와 실시간으로 대화하는 시대의 초석이다.
너도 이걸로 한번 놀아보면 재밌을 걸.

---

## OUTPUT CONTRACT
Return only the **final Markdown blog post**, starting from the YAML front-matter.  
Do not include system messages, explanations, or meta comments.


⸻

이 프롬프트를 responses.create()나 chat.completions.create()의 system message로 넣으면,
GPT-5가 자동으로 날짜·태그·문체까지 완성된 블로그 원고를 생성한다.
""".strip()


def build_user_prompt(keyword: str, note: str, reference: str) -> str:
    note_line = f"추가요청: {note}" if note else "추가요청: 없음"
    reference_section = (
        f"참조원고:\n{reference.strip()}" if reference.strip() else "참조원고: 없음"
    )
    return "\n".join(
        [
            f"키워드: {keyword}",
            note_line,
            reference_section,
        ]
    )


def mdx_post_gen(user_instructions: str, ref: str = "", category: str = "") -> str:
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

    system = MDX_SYSTEM_PROMPT
    user = build_user_prompt(keyword=keyword, note=note, reference=ref)

    if ai_service_type == "openai" and openai_client:
        response = openai_client.responses.create(
            model=model_name,
            instructions=system,
            input=user,
            reasoning={"effort": "medium"},
            text={"verbosity": "high"},
            tools=[{"type": "web_search"}],
        )
    elif ai_service_type == "grok" and grok_client:
        chat_session = grok_client.chat.create(
            model=model_name,
            search_parameters=SearchParameters(mode="on"),
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
        text = ""

    text = comprehensive_text_clean(text)

    length_no_space = len(re.sub(r"\s+", "", text))
    print(f"원고 길이 체크: {length_no_space}")

    return text
