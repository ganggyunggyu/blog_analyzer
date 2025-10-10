from __future__ import annotations
import json
from textwrap import dedent
from _constants.Model import Model
from config import grok_client
from xai_sdk.chat import system as grok_system_message
from xai_sdk.chat import user as grok_user_message


model_name: str = Model.GROK_4_NON_RES  # Grok Fast 사용


def get_문장해체(ref: str, model: str = model_name):
    """
    참조 원고를 분석해 Grok 최적화 JSON 메타데이터 반환 (상품/서비스 + 노출 원인 학습)

    Args:
        ref: 참조 원고 텍스트
        model: Grok 모델명 (기본: GROK_4_FAST)

    Returns:
        JSON 형식 메타데이터 (화자/구성/부제/스타일)
    """
    if not ref:
        return "{}"

    system = """
You are an expert in text analysis for blog content. Analyze the manuscript to extract metadata for style, structure, and key themes (product/service details, exposure reasons like episodes/benefits). Output ONLY JSON, no extra text.
""".strip()

    schema = {
        "speaker_guidance": {
            "keyword": "원고 주제/핵심 상품",
            "persona": "화자의 연령/성별/특징",
            "tone": "구어체/격식체, 주요 화법",
            "frequent_phrases": ["자주 등장하는 표현 나열"],
        },
        "structure_guidance": {
            "intro": "도입부 요약",
            "body": "중간 전개 요약 (노출 원인: 에피소드/혜택 강조)",
            "conclusion": "마무리 요약",
        },
        "subtitles_analysis": {
            "description": "원고 흐름/주제를 기반으로 부제 5개 생성 (10자 내외, 업체명 금지, 지역명 유동적 변경)",
            "subtitles": [
                "1. 부제 1",
                "2. 부제 2",
                "3. 부제 3",
                "4. 부제 4",
                "5. 부제 5",
            ],
        },
        "style_details": ["문단 길이, 문체, 리듬, 에피소드 활용 패턴"],
    }

    prompt = dedent(
        f"""
    다음은 블로그 원고입니다.

    [원고]
    - 업체명 언급 금지
    {ref}

    [요청]
    아래 JSON 스키마에 맞게 메타데이터 추출. 상품/서비스 정보와 노출 원인(에피소드, 혜택 강조) 반영.

    {json.dumps(schema, ensure_ascii=False, indent=2)}

    JSON만 반환.
    """
    ).strip()

    # Grok API 호출 (non-reasoning 모드 기본)
    if grok_client:
        chat_session = grok_client.chat.create(model=model)
        chat_session.append(grok_system_message(system))
        chat_session.append(grok_user_message(prompt))
        response = chat_session.sample()
        text = getattr(response, "content", "") or ""

        return text


# 사용 예시
if __name__ == "__main__":
    sample_ref = """
    ▶ 복용 후 변화 과정
    l 1주차: 뒤척이는 시간 감소
    l 2주차: 새벽 각성 횟수 감소
    l 3주차: 아침 피로감 완화
    l 4주차: 낮 집중력 회복
    """
    result = get_문장해체(sample_ref)
    print("✅ Grok JSON 메타데이터 생성 완료")
    print(result)  # JSON 출력 (mock 예시)
