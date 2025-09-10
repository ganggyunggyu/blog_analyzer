from __future__ import annotations

import time
import re
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.concurrency import run_in_threadpool

from config import UPSTAGE_API_KEY, solar_client
from mongodb_service import MongoDBService
from schema.generate import GenerateRequest
from utils.get_category_db_name import get_category_db_name
from utils.query_parser import parse_query
from _prompts.get_kkk_prompts import KkkPrompt
from _prompts.service.get_ref_prompt import get_ref_prompt
from utils.text_cleaner import comprehensive_text_clean
from utils.format_paragraphs import format_paragraphs


router = APIRouter()

SOLAR_MODEL_NAME = "solar-pro2"


def _build_solar_prompts(
    keyword: str, note: Optional[str], ref: str, category: str
) -> tuple[str, str]:
    parsed_note = note or ""

    참조_분석_프롬프트 = get_ref_prompt(ref)
    system = KkkPrompt.get_kkk_system_prompt_v2(category)

    user = f"""

    ---

[핵심 키워드]
{keyword}

아래의 정보를 토대로 핵심 키워드 기반의 블로그 원고를 작성해줘


---

    필수로 **공백제외 글자 길이 4000단어 이상**
**Solar Pro 2 API 프롬프트 예시**  
*(4000자 이상, 자연스러운 스토리텔링, 부제 통합형)*  
[하단은 모두 예시임으로 독창적인 스토리 텔링을 작성해야함]

---

**프롬프트:**  
"20대 초반 프리랜서 디자이너의 1인칭 시점으로 체중 감량 이야기를 풀어주세요. 출산 대신 대학 졸업 후 취업 스트레스로 15kg 체중이 증가했고, 야근과 불규칙한 식습관으로 인해 복부 비만과 식탐에 시달렸다는 설정을 추가해주세요. 다음 키워드를 반드시 포함하되, 부제처럼 나열하지 말고 문맥에 자연스럽게 녹여내세요.  

- **GLP-1 유사체 주사제의 포만감 유지 메커니즘** (예: "포만감을 오래 유지시켜 주는 거예요"를 대화체 표현으로 변환)  
- **국내 처방 조건 및 비용** (2023년 10월 국내 출시, 처방비 1만 원 등 실제 정보 기반)  
- **유산균과의 병행 효과** (장내 미생물 균형 개선 경험)  
- **요요 현상 방지 전략** (생활 패턴 조정 사례)  
- **식욕억제제 복용 초기 부작용** (두통, 구토 등 구체적 증상)  

**조건:**  
1. 블로거 신상은 "26세 프리랜서 김민지"로 고정하되, 직업적 특성(예: 디자인 작업 중 간식 중독)을 스토리에 반영.  
2. 부제 대신 소제목 형식으로 내용을 구분하되, 문단 시작 부분에 괄호 없이 간결하게 표기 (예: *'첫 번째 전환점: GLP-1과의 만남'*).  
3. 대괄호 `[ ]` 절대 사용 금지.  
4. '20대 직장인'과 같은 일반화된 표현 대신 구체적 경험(예: "클라이언트 미팅 전 긴장감으로 폭식이 반복됐다")을 강조.  
5. 전문가 조언이나 통계보다는 개인적 체험에 초점 (예: "유산균을 먹으면서 주사에 대한 의존도가 줄었다").  

**시작 문구:**  
"모니터 앞에서 초콜릿 바를 뜯어먹던 어느 날, 체중계 숫자가 70kg을 넘겼습니다. 프리랜서 3년 차, 프로젝트가 밀릴 때마다 스트레스로 야식을 찾았고..."  

---

**생성 예시 (API 출력 시)**  
> *"첫 번째 전환점: GLP-1과의 만남*  
의사 선생님은 '포만감을 조절하는 호르몬'을 언급하며 주사 치료를 권유했습니다. 처음엔 가격이 부담됐죠. 2023년 10월 국내 출시된 약제라 처방비가 1만 원인데, 보험 적용이 안 된다는 게 아쉬웠어요. 하지만 2주 만에 식탐이 줄어들며 점심 식사 후 디저트 생각이 사라졌습니다.  

*부작용과의 싸움*  
처음 3일은 두통과 메스꺼움으로 고생했어요. 식욕억제제를 병행했더니 증상이 겹치며 구토까지 했습니다. 의사에게 상담 후 복용량을 조절했고, 2주 뒤부터는 점차 적응됐죠.  

*유산균이 가져온 변화*  
의사 추천으로 GLP-1 유산균 제품을 추가했어요. 장운동이 활발해지면서 복부 팽만감이 줄었고, 주사만으로 느끼던 포만감이 더 오래 유지되는 것 같았습니다.  

*요요를 피하는 법*  
지금은 아침 30분 스트레칭으로 하루를 시작합니다. 디자인 작업 중 간식 대신 녹차나 아몬드를 먹으며 습관을 바꿨죠. 체중계 숫자에 집착하지 않고, 옷 사이즈 변화로 성장을 확인하는 게 핵심이었어요."  

---  
**프롬프트 핵심:**  
- **구체적 캐릭터 설정**으로 공감대 형성  
- **키워드 문맥 통합**을 통한 자연스러운 정보 전달  
- **개인적 경험 강조**로 독자 참여 유도  
- **소제목 + 단락 구분**으로 가독성 확보

---
[참조 원고 분석]

{ref}
{참조_분석_프롬프트}



---

[필수로 이행해야하는 추가 요청]
{parsed_note}

---
[금기사항]

짧은 원고라면 다시 작성
마크다운을 포함한 ""같은 의미없는 특수문자 금지

---
""".strip()

    return system, user


def solar_generate(user_instructions: str, ref: str = "", category: str = "") -> str:

    if not UPSTAGE_API_KEY:
        raise ValueError("UPSTAGE_API_KEY가 설정되어 있지 않습니다. .env를 확인하세요.")

    parsed = parse_query(user_instructions)
    keyword = parsed.get("keyword")
    if not keyword:
        raise ValueError("키워드가 없습니다.")

    system, user = _build_solar_prompts(keyword, parsed.get("note"), ref, category)

    start_ts = time.time()
    print("원고작성 시작")
    response = solar_client.chat.completions.create(
        model=SOLAR_MODEL_NAME,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        reasoning_effort="high",
    )

    choices = getattr(response, "choices", []) or []
    if not choices or not getattr(choices[0], "message", None):
        raise RuntimeError("SOLAR가 유효한 choices/message를 반환하지 않았습니다.")

    text: str = (choices[0].message.content or "").strip()
    if not text:
        raise RuntimeError("SOLAR가 빈 응답을 반환했습니다.")

    text = format_paragraphs(text)
    text = comprehensive_text_clean(text)
    length_no_space = len(re.sub(r"\s+", "", text))
    print(f"원고 길이 체크: {length_no_space}")
    elapsed = time.time() - start_ts
    print(f"원고 소요시간: {elapsed:.2f}s")
    print("원고작성 완료")
    return text


@router.post("/generate/solar")
async def generate_solar(request: GenerateRequest):
    """
    Upstage SOLAR로 원고 생성. kkk 프롬프트를 사용합니다.
    """
    service = request.service.lower()
    keyword = request.keyword.strip()
    ref = request.ref

    category = get_category_db_name(keyword=keyword)
    db_service = MongoDBService()
    db_service.set_db_name(db_name=category)

    # 디버그 출력: 어떤 서비스/모델/키워드/참조 여부로 실행하는지 표시
    is_ref = bool(ref and ref.strip())
    print(
        f"[GEN] service={service} | model={SOLAR_MODEL_NAME} | category={category} | keyword={keyword} | hasRef={is_ref}"
    )

    try:
        manuscript = await run_in_threadpool(
            solar_generate, user_instructions=keyword, ref=ref, category=category
        )

        if not manuscript:
            raise HTTPException(status_code=500, detail="SOLAR 원고 생성 실패")

        current_time = time.time()
        document = {
            "content": manuscript,
            "timestamp": current_time,
            "engine": SOLAR_MODEL_NAME,
            "service": service or "solar",
            "category": category,
            "keyword": keyword,
        }

        try:
            db_service.insert_document("manuscripts", document)
            document["_id"] = str(document.get("_id", ""))
        except Exception as e:
            # 저장 실패는 경고만 남기고 본문은 반환
            print(f"SOLAR 데이터베이스 저장 실패: {e}")

        return document
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"SOLAR 원고 생성 중 오류: {e}")
    finally:
        if db_service:
            db_service.close_connection()
