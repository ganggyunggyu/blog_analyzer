from __future__ import annotations
import re
import time

from openai import OpenAI
from _prompts.constants import alticle_nat_prompt, article_flow_prompt
from _prompts.service.get_mongo_prompt import get_mongo_prompt
from config import OPENAI_API_KEY
from _constants.Model import Model
from _prompts.get_kkk_prompts import KkkPrompt
from _prompts.service.get_ref_prompt import get_ref_prompt
from utils.format_paragraphs import format_paragraphs
from utils.query_parser import parse_query
from utils.text_cleaner import comprehensive_text_clean


model_name: str = Model.GPT5
min_length: int
max_length: int

client = OpenAI(api_key=OPENAI_API_KEY)


def kkk_gen(user_instructions: str, ref: str = "", category: str = "") -> str:
    """
    Returns:
        생성된 원고 텍스트 (str)

    Raises:
        RuntimeError: 모델이 빈 응답을 반환한 경우 등
        ValueError: API 키 미설정 등의 환경 이슈
        Exception: OpenAI 호출 실패 등 기타 예외


    Lib:
        [참조원고 데이터]
        {ref_prompt}

        위 데이터를 토대로 블로그 바이럴 마케팅 원고를 작성해

        [원고 작성 규칙]

        {default_prompt}

        {alticle_nat_prompt}

        {article_flow_prompt}
    """

    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY가 설정되어 있지 않습니다. .env를 확인하세요.")

    parsed = parse_query(user_instructions)
    keyword, note = parsed.get("keyword", ""), parsed.get("note", "")
    print(keyword, note)
    # if category == "legalese":
    # model_name = Model.GPT5
    # else:
    # model_name = Model.GPT5_CHAT

    if not parsed["keyword"]:
        raise ValueError("키워드가 없습니다.")

    if model_name == Model.GPT5_CHAT:
        [min_length, max_length] = [3000, 3200]
    else:
        [min_length, max_length] = [2400, 2600]

    default_prompt = KkkPrompt.kkk_prompt_gpt_5(
        keyword=parsed["keyword"],
        min_length=min_length,
        max_length=max_length,
        category=category,
    )
    mongo_data = get_mongo_prompt(category)
    ref_prompt = get_ref_prompt(ref)

    system = KkkPrompt.get_kkk_system_prompt_v2()
    user: str = (
        f"""

[참조원고]
{ref_prompt}
[키워드]
{parsed.get('keyword', '')}

[원고 작성 규칙]
"" 쓰지마
마무리: << 이런거 하지마 문장체로 써 요약해보자면 마무리 해보자면 이런식으로
비용: 병원비와 1펜 단가, 부대비용까지 합치면 << 이런거 하지마 자연스러운 문장형태로 작성해

---
[라이브러리]
- 꼭 이 라이브러리 규칙을 참고해서 원고를 작성해야해
{mongo_data}
---

[유저 추가 요청]
{parsed.get('note', '')}

---
""".strip()
    )

    try:
        start_ts = time.time()
        is_ref = len(ref) != 0
        print(
            f"[GEN] service={'test-kkk'} | model={model_name} | category={category} | keyword={user_instructions} | is_ref={is_ref}"
        )
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {
                    "role": "system",
                    "content": """
너는 입력된 템플릿과 라이브러리를 받아, 템플릿의 [슬롯]을 의미가 맞는 라이브러리 값으로 자연스럽게 채워 넣는 역할을 한다.  
반드시 유저가 보내는 키워드를 중심으로 원고를 작성하도록 한다.
동일 슬롯은 중복되지 않도록 변형·순환하며, 문맥이 맞지 않으면 일반 어휘를 보완하되 과장·확정 표현은 금지한다.  
출력은 템플릿의 구조와 길이를 유지하되 마크다운·대괄호·링크 없이 완성된 본문만 반환한다.
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
            print(
                f"[🔍 Token Usage] "
                f"Prompt: {in_tokens:,}  |  "
                f"Completion: {out_tokens:,}  |  "
                f"Total: {total_tokens:,}"
            )
        choices = getattr(response, "choices", []) or []
        if not choices or not getattr(choices[0], "message", None):
            raise RuntimeError("모델이 유효한 choices/message를 반환하지 않았습니다.")

        text: str = (choices[0].message.content or "").strip()
        if not text:
            raise RuntimeError("모델이 빈 응답을 반환했습니다.")

        text = format_paragraphs(text)
        text = comprehensive_text_clean(text)

        length_no_space = len(re.sub(r"\s+", "", text))
        elapsed = time.time() - start_ts
        print(f"원고 길이 체크: {length_no_space}")
        print(f"원고 소요시간: {elapsed:.2f}s")
        print("원고작성 완료")

        return text

    except Exception as e:
        raise
