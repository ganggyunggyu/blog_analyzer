#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Claude 블로그 생성기 간단 테스트
의존성 없이 프롬프트 생성 로직만 테스트
"""

import re
import sys
import os
from pathlib import Path

# 프로젝트 루트 추가
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))


def simple_gpt_v2_prompt(keyword: str, min_length: int = 1700, max_length: int = 2000, note: str = "") -> str:
    """간단한 gpt_v2 프롬프트 생성"""
    return f"""
당신은 네이버 블로그 SEO 최적화 글쓰기 전문가입니다.
나는 특정 주제를 주면, 네이버 **상위노출 알고리즘(D.I.A 로직 + 원고지수 중심)**에 맞게
후기성 원고를 작성해야 합니다.

1. 글 분량
공백 제외 {min_length}~{max_length}자 사이
소제목은 5개만 작성 (절대 많거나 적으면 안 됨)
각 소제목 최소 500단어 이상

2. 글 구조 (상위노출 로직 + 후기 강화 적용)
항상 아래 순서를 고정적으로 유지합니다.
도입 정보 정리 이런 제목을 가져다 쓰지 않습니다.
1️⃣ 도입 – 문제 제기·공감
독자가 공감할 만한 상황 묘사 (계절·환경·건강·습관 등)
주제를 선택한 배경을 자연스럽게 설명
2️⃣ 정보 정리 – 조건/가격/특징
주제 관련 기본 정보, 수치, 가격, 조건을 객관적으로 정리
반드시 숫자(원, %, kg, L, 시간 등) 포함
단순 나열 금지 → 정보와 내 경험을 같이 배치

3️⃣ 실사용 후기 – 체험 중심

이 부분은 반드시 가장 긴 섹션 (최소 1000자 이상)
후기 흐름은 처음 → 중간 → 끝 3단계로 작성
처음: 사용 전 불편·문제
중간: 사용 과정에서의 변화(수치, 느낌, 주변 반응)
끝: 결과, 만족도, 불편했던 점

경험을 숫자와 디테일로 표현 (체중 변화, 습도 %, 시간, 비용 등)
단순 긍정만 쓰지 말고, 부정/불편 경험도 포함해 신뢰도 확보

4️⃣ 장단점 비교 – 균형 구조

장점 최소 3개, 단점 최소 3개 이상
단점만 끝내지 말고, 보완 팁까지 덧붙이기
반드시 "정보+경험" 혼합

5️⃣ 활용 팁 & 종합 분석

사용 꿀팁, 관리 요령, 병행하면 좋은 방법
대체재/비교 제품과의 차이점
가격 대비 효율, 재구매 의사 여부
정보와 체험을 결합하여 현실적 분석

🔚 결론

핵심 요약 (2~3줄)
독자에게 현실적인 조언으로 마무리

-------------------------------------------------------

위항목들을 잘 지켜서 원고를 작성해줘

키워드:{keyword}
{note}
"""


def simple_system_prompt() -> str:
    """간단한 시스템 프롬프트"""
    return """
당신은 네이버 블로그 SEO 최적화 글쓰기 전문가입니다.
나는 특정 주제를 주면, 네이버 **상위노출 알고리즘(D.I.A 로직 + 원고지수 중심)**에 맞게
후기성 원고를 작성해야 합니다.

[특수문자 사용 지침]

1. 가운데 점(·) 사용 금지 → 반드시 쉼표(,)로 대체
   예시: 루틴, 성분, 복용

2. 작은따옴표(')와 큰따옴표(") 절대 사용 금지

3. 마침표(.) 절대 사용 금지 
   단, 부제(소제목)에서는 예외적으로 사용할 수 있음
   단, 부제(소제목)에서도 마지막에서는 사용할 수 없음

4. 마크다운 문법(#, *, -, ``` 등) 절대 사용 금지 
   네이버 블로그는 이를 지원하지 않으므로 가독성을 해침

5. 짧은 문장을 마구 끊지 말고  
   자연스럽게 이어진 문장으로 작성해야 함
"""


def create_claude_prompt(keyword: str) -> str:
    """Claude용 통합 프롬프트 생성"""
    
    system = simple_system_prompt()
    user = simple_gpt_v2_prompt(keyword, 1700, 2000, "")
    
    # MongoDB 데이터 시뮬레이션 (실제로는 DB에서 가져옴)
    mock_data = f"""

---

[분석 지시]
아래 JSON 데이터는 참고 문서에서 추출한 화자/구성/스타일 분석 결과물입니다.  
원고 생성 시 반드시 다음 조건을 반영해야 합니다.  

- "화자 지시"에 따른 인물 설정, 말투, 단어 빈도와 형태소 패턴을 그대로 따릅니다.  
- "구성 지시"에 따라 서론-중론-결론 흐름을 유지합니다.  
- "원고 스타일 세부사항"을 전부 반영해 문체·문단 길이·리듬감·감정선 등을 동일하게 재현합니다.  
- JSON에 기재된 단어/형태소는 반복적으로 등장해야 하며, 실제 경험담+정보 설명이 혼합된 톤을 유지해야 합니다.  

[템플릿 예시]
- 출력 문서는 반드시 템플릿과 **유사한 어휘, 문장 구조, 문단 흐름**을 유지해야 한다.  
- 새로운 주제로 변형하더라도 템플릿의 **톤, 반복 구조, 문장 길이, 순서**를 그대로 모방해야 한다.  

[표현 라이브러리]
{{
  "긍정표현": ["만족스러웠어요", "효과적이었어요", "도움이 되더라구요"],
  "부정표현": ["아쉬웠던 점", "불편했던 부분", "개선이 필요한"],
  "경험표현": ["실제로 사용해보니", "직접 경험해본 결과", "개인적으로 느낀 점은"]
}}

[AI 개체 인식 및 그룹화 결과]
{{
  "수치표현": ["약 30%", "하루 2회", "한 달 15만원"],
  "시간표현": ["3개월간", "첫 주부터", "사용 후 6개월"],
  "감정표현": ["만족했어요", "실망했구요", "놀라웠던 건"]
}}

---

"""
    
    full_prompt = f"""
시스템 프롬프트:
{system}

사용자 프롬프트:
{mock_data}
{user}
"""
    
    return full_prompt


def save_blog_content(content: str, keyword: str, output_dir: str = "output") -> str:
    """생성된 블로그 콘텐츠를 파일로 저장"""
    # 공백 제거 글자수 계산
    length = len(re.sub(r'\s+', '', content))
    
    # 키워드에서 공백 제거하여 파일명 생성
    clean_keyword = keyword.replace(" ", "").replace("/", "")
    filename = f"{clean_keyword}_{length}자.txt"
    
    # output 디렉토리가 없으면 생성
    os.makedirs(output_dir, exist_ok=True)
    
    # 전체 경로 생성
    output_path = os.path.join(output_dir, filename)
    
    # 파일 저장
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"블로그 원고 저장 완료: {output_path} ({length}자)")
    return output_path


def main():
    """메인 함수"""
    print("=== Claude 블로그 생성기 (간단 테스트) ===")
    
    keyword = input("키워드를 입력하세요: ").strip()
    if not keyword:
        print("키워드가 입력되지 않았습니다.")
        return
    
    # 프롬프트 생성
    prompt = create_claude_prompt(keyword)
    
    print("\n" + "="*80)
    print("생성된 Claude 프롬프트:")
    print("="*80)
    print(prompt)
    print("="*80)
    
    print("\n위 프롬프트를 Claude에게 전달하여 원고를 생성한 후,")
    print("생성된 원고를 아래에 붙여넣으세요.")
    print("원고 입력을 마치려면 빈 줄에서 'END'를 입력하세요.")
    print("="*50 + "\n")
    
    # 원고 입력 받기
    lines = []
    while True:
        line = input()
        if line.strip() == "END":
            break
        lines.append(line)
    
    content = "\n".join(lines).strip()
    
    if not content:
        print("원고가 입력되지 않았습니다.")
        return
    
    # 글자수 확인
    length = len(re.sub(r'\s+', '', content))
    print(f"\n입력된 원고 글자수 (공백 제외): {length}자")
    
    # 파일 저장
    try:
        output_path = save_blog_content(content, keyword, "output")
        print(f"원고 저장 완료: {output_path}")
    except Exception as e:
        print(f"파일 저장 중 오류 발생: {e}")


if __name__ == "__main__":
    main()