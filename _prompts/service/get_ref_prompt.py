from __future__ import annotations
from analyzer.request_문장해체분석기 import get_문장해체


def get_ref_prompt(ref: str) -> str:
    """
    참조 원고를 분석하여 GPT-5 최적화 프롬프트 생성

    Args:
        ref: 참조할 원고 텍스트

    Returns:
        GPT-5에 최적화된 XML 구조의 참조 프롬프트
    """

    # 문장 해체 분석 수행
    참조분석 = get_문장해체(ref)

    # GPT-5 최적화 XML 구조 프롬프트
    ref_prompt = f"""
<reference_document_analysis>
    <analysis_metadata>
        <purpose>참조 문서 스타일 추출 및 변형 적용</purpose>
        <priority>스타일 모방 > 내용 참조 > 직접 인용</priority>
    </analysis_metadata>
    
    <original_document>
        <content><![CDATA[{ref}]]></content>
    </original_document>
    
    <style_analysis>
        <parsed_elements><![CDATA[{참조분석}]]></parsed_elements>
    </style_analysis>
    
    <transformation_rules priority="mandatory">
        <content_transformation>
            <rule id="1" priority="critical">
                업체명/브랜드명 절대 포함 금지 → 익명화 필수
            </rule>
            <rule id="2" priority="critical">
                동일 문장 복사 금지 → 의미만 차용, 문장 재구성
            </rule>
            <rule id="3" priority="high">
                구조적 요소 변형 예시:
                - "▶ 복용 후 변화 과정" → "◆ 사용 후 개선 단계"
                - "l 1주차:" → "• 첫째 주:"
                - 숫자/기간 변경: 1-2-3-4주 → 1-2-4-8주
            </rule>
        </content_transformation>
        
        <style_extraction>
            <element name="narrator_voice">
                <extract>화자 특성, 말투, 어휘 선택</extract>
                <transform>유사하되 독창적인 페르소나 생성</transform>
            </element>
            
            <element name="structure_flow">
                <extract>서론-중론-결론 구성비</extract>
                <maintain>전체적 흐름 유지</maintain>
            </element>
            
            <element name="linguistic_patterns">
                <extract>문장 길이, 리듬, 단락 구조</extract>
                <apply>패턴 유지하며 내용 변경</apply>
            </element>
            
            <element name="emotional_tone">
                <extract>감정선, 강조점, 호흡</extract>
                <preserve>독자 공감 포인트</preserve>
            </element>
        </style_extraction>
    </transformation_rules>
    
    <application_guidelines>
        <mandatory_requirements>
            1. 참조분석의 화자 지시 → 변형된 인물 설정
            2. 구성 지시 → 동일 구조, 다른 내용
            3. 스타일 세부사항 → 문체만 유지
            4. 형태소 패턴 → 반복하되 변주
        </mandatory_requirements>
        
        <quality_checks>
            <uniqueness>표절 검사 통과 수준</uniqueness>
            <similarity>스타일 유사도 70-80%</similarity>
            <readability>자연스러운 흐름 유지</readability>
        </quality_checks>
        
        <tone_balance>
            <information weight="40%">정보 전달</information>
            <experience weight="40%">경험 공유</experience>
            <emotion weight="20%">감정 공감</emotion>
        </tone_balance>
    </application_guidelines>
    
    <examples_transformation>
        <example type="structure">
            <original>
                ▶ 복용 후 변화 과정
                l 1주차: 뒤척이는 시간 감소
                l 2주차: 새벽 각성 횟수 감소
            </original>
            <transformed>
                ◆ 사용 후 개선 단계
                • 첫째 주: 수면 질 향상 시작
                • 둘째 주: 깊은 잠 시간 증가
            </transformed>
        </example>
        
        <example type="expression">
            <original>효과가 정말 놀라웠어요</original>
            <transformed>변화가 기대 이상이었습니다</transformed>
        </example>
    </examples_transformation>
    
    <fallback_behavior>
        <if_no_reference>기본 스타일 가이드 적용</if_no_reference>
        <if_analysis_fails>일반적인 블로그 톤 사용</if_analysis_fails>
    </fallback_behavior>
</reference_document_analysis>
"""
    return ref_prompt


# 보조 함수 (선택적 구현)
def validate_ref_prompt(ref_prompt: str) -> bool:
    """
    생성된 참조 프롬프트 유효성 검증

    Args:
        ref_prompt: 검증할 프롬프트

    Returns:
        유효성 여부
    """
    required_tags = [
        "<reference_document_analysis>",
        "<transformation_rules>",
        "<application_guidelines>",
    ]

    return all(tag in ref_prompt for tag in required_tags)


# 사용 예시
if __name__ == "__main__":
    sample_ref = """
    ▶ 복용 후 변화 과정
    l 1주차: 뒤척이는 시간 감소
    l 2주차: 새벽 각성 횟수 감소
    l 3주차: 아침 피로감 완화
    l 4주차: 낮 집중력 회복
    """

    optimized_prompt = get_ref_prompt(sample_ref)

    # 유효성 검증
    if validate_ref_prompt(optimized_prompt):
        print("✅ GPT-5 최적화 프롬프트 생성 완료")
    else:
        print("❌ 프롬프트 생성 오류")
