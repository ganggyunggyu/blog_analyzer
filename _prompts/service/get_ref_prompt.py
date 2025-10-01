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
<reference_document_usage>
  <!-- 참조 문서가 제공된 경우에만 활성화 -->
  
  <purpose>
    참조 문서의 스타일, 톤, 흐름을 학습하여 유사한 느낌의 새로운 글 작성
  </purpose>
  
  <original_document>
    {ref}
  </original_document>
  
  <style_analysis_result>
    {참조분석}
  </style_analysis_result>
  
  <critical_rules priority="absolute">
    <!-- 상위 프롬프트 규칙보다 우선하지 않음 -->
    
    <rule_1>
      업체명/브랜드명 절대 포함 금지
      → 참조 문서에 있어도 익명화 또는 일반 명사로 대체
    </rule_1>
    
    <rule_2>
      동일 문장 복사 절대 금지
      → 의미만 참고, 완전히 다른 문장으로 재작성
    </rule_2>
    
    <rule_3>
      상위 프롬프트의 금지 형식 준수
      → 참조 문서에 특수문자(•, ▶ 등)가 있어도 사용 금지
      → 대신 숫자 넘버링(1. 2. 3.)이나 자연스러운 단락 구분 사용
    </rule_3>
  </critical_rules>
  
  <what_to_extract>
    <!-- 참조 문서에서 배울 것들 -->
    
    <style_elements>
      ✓ 화자의 목소리 (말투, 어휘 선택, 호칭)
      ✓ 문장 길이와 리듬 (짧은/긴 문장 교차 패턴)
      ✓ 단락 구조 (몇 문장으로 단락을 구성하는지)
      ✓ 감정선 (언제 진지, 언제 가볍게)
      ✓ 전개 방식 (시간순/중요도순/문제-해결)
    </style_elements>
    
    <structure_flow>
      ✓ 도입-전개-마무리 비율
      ✓ 소제목 간 내용 균형
      ✓ 정보와 경험담의 배분
    </structure_flow>
  </what_to_extract>
  
  <what_to_transform>
    <!-- 반드시 변경해야 할 것들 -->
    
    <content_variation>
      ✗ 화자 페르소나: 완전히 다른 인물로 변경
      ✗ 구체적 경험: 새로운 에피소드 창작
      ✗ 숫자/기간: 다른 값으로 변경 (예: 1-2-3주 → 2-4-8주)
      ✗ 고유명사: 모두 변경 또는 익명화
      ✗ 문장 표현: 의미는 유사, 문장은 완전히 다르게
    </content_variation>
  </what_to_transform>
  
  <application_method>
    <!-- 실제 적용 방법 -->
    
    참조 문서를 다음과 같이 활용하세요:
    
    1. 톤과 분위기 파악
       → 격식체인가 구어체인가? 진지한가 가벼운가?
    
    2. 구성 방식 이해
       → 어떤 순서로 정보를 전달하는가?
    
    3. 표현 패턴 학습
       → 어떤 연결어를 자주 쓰는가? 문장 호흡은?
    
    4. 새로운 내용 창작
       → 학습한 스타일로 완전히 다른 내용 작성
    
    결과: 같은 필자가 쓴 것 같지만 내용은 전혀 다른 글
  </application_method>
  
  <quality_targets>
    <!-- 추상적 수치 대신 구체적 기준 -->
    
    <style_similarity>
      참조 문서와 "같은 사람이 쓴 것 같다"는 느낌이 들어야 함
      하지만 문장이나 표현은 완전히 달라야 함
    </style_similarity>
    
    <content_originality>
      표절 검사 도구로 확인 시 중복 문장 0%
      핵심 아이디어만 공유, 표현은 100% 독창적
    </content_originality>
    
    <tone_balance>
      참조 문서의 정보:경험:감정 비율을 유지
      예: 참조가 정보 위주면 → 새 글도 정보 위주
          참조가 감성 위주면 → 새 글도 감성 위주
    </tone_balance>
  </quality_targets>
  
  <transformation_examples>
    <!-- 구체적 변환 예시 -->
    
    <example_1>
      참조: "복용 1주차부터 효과를 느꼈어요"
      변환: "사용 초반에 변화가 시작되더라구요"
      (의미 유사, 표현 완전 변경)
    </example_1>
    
    <example_2>
      참조: "A 브랜드 제품을 구매했습니다"
      변환: "비슷한 제품을 알아보게 되었어요"
      (브랜드명 제거, 일반화)
    </example_2>
    
    <example_3>
      참조: "▶ 사용 후기\nl 1주차: 개선\nl 2주차: 효과"
      변환: "사용하면서 느낀 점\n\n1주 차에는 조금씩 나아지더니, 2주쯤 되니 확실히 달라졌어요."
      (특수문자 제거, 자연스러운 서술로 변경)
    </example_3>
  </transformation_examples>
  
  <conflict_resolution>
    <!-- 충돌 시 해결 규칙 -->
    
    만약 "참조 문서 스타일 유지"와 "상위 금지 규칙"이 충돌하면:
    → 항상 상위 금지 규칙을 우선합니다
    → 참조 문서에 금지된 형식이 있어도 사용하지 마세요
    → 대신 허용된 대체 방법을 찾으세요
    
    예: 참조에 • 불릿이 있어도 → 1. 2. 3. 숫자로 대체
        참조에 **볼드**가 있어도 → 자연스러운 강조 표현으로 대체
  </conflict_resolution>
  
</reference_document_usage>
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
