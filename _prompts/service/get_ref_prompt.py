from __future__ import annotations
import json
from analyzer.request_문장해체분석기 import get_문장해체


def get_ref_prompt(ref: str) -> str:
    """
    참조 원고를 분석하여 Grok 최적화 JSON 프롬프트 생성 (간소화 버전)

    Args:
        ref: 참조할 원고 텍스트 (상품/서비스 설명 포함)

    Returns:
        Grok에 최적화된 JSON 구조의 참조 프롬프트
    """
    if len(ref) == 0:
        return ""

    참조분석 = get_문장해체(ref)

    ref_prompt = {
        "reference_document_usage": {
            "purpose": "참조 문서의 스타일/톤/흐름 학습 + 상품/서비스 설명으로 AI 지식 보완. 노출 원인(상세 에피소드, 혜택 강조) 따라 새 글 작성.",
            "original_document": ref,
            "style_analysis_result": 참조분석,
            "critical_rules": [
                "업체명/브랜드명 익명화 (e.g., 'A 제품' → '비슷한 제품')",
                "문장 복사 금지: 의미만 참고, 재작성",
                "상위 금지 형식 우선: 특수문자 피함 (e.g., 불릿 → 숫자), 참조 형식 무시",
            ],
            "what_to_extract": {
                "elements": [
                    "화자 목소리 (구어체, 호칭)",
                    "문장 리듬 (짧/긴 교차)",
                    "감정선 (진지→가벼움)",
                    "전개 (시간순/문제-해결)",
                    "비율 (도입-전개-마무리)",
                ]
            },
            "what_to_transform": [
                "화자 페르소나: 새 인물 창작",
                "경험/숫자: 새 에피소드 (e.g., 1주 → 2주, 노출 원인 에피소드 강조)",
                "고유명사: 변경/익명화 (상품 설명 일반화)",
            ],
            "application_method": [
                "1. 톤/구성 파악 (구어체? 에피소드 위주?)",
                "2. 표현 학습 (연결어, 호흡)",
                "3. 새 창작: 상품 설명 + 노출 원인(상세 혜택 에피소드) 따라 작성",
                "Quality: 같은 필자 느낌 (스타일 80% 유사), 내용 100% 독창 (중복 0%)",
            ],
            "transformation_examples": [
                {
                    "original": "복용 1주차부터 효과",
                    "transformed": "사용 초반에 변화 시작 (에피소드 추가)",
                },
                {
                    "original": "A 브랜드 구매",
                    "transformed": "비슷한 제품 알아봄 (브랜드 제거)",
                },
                {
                    "original": "▶ 1주: 개선",
                    "transformed": "1주 차에 조금씩 나아짐 (자연 서술)",
                },
            ],
        }
    }
    return json.dumps(ref_prompt, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    sample_ref = """
    ▶ 복용 후 변화 과정
    l 1주차: 뒤척이는 시간 감소
    l 2주차: 새벽 각성 횟수 감소
    l 3주차: 아침 피로감 완화
    l 4주차: 낮 집중력 회복
    """
    optimized_prompt = get_ref_prompt(sample_ref)
    print("✅ Grok 최적화 프롬프트 생성 완료")
    print(optimized_prompt)
