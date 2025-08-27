#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Claude를 사용한 블로그 원고 생성 스크립트
MongoDB 데이터를 활용하여 gpt_v2 프롬프트 기반으로 원고 생성
"""

import re
import sys
import os
from pathlib import Path

# 프로젝트 루트 추가
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from claude.claude_service import generate_blog_content, save_blog_content
from prompts.get_system_prompt import get_system_prompt_v2


def create_blog_post(keyword: str, ref: str = "", note: str = "") -> str:
    """
    블로그 포스트 생성
    
    Args:
        keyword: 블로그 키워드
        ref: 참조 문서 (선택사항)
        note: 추가 요청사항 (선택사항)
    
    Returns:
        생성된 블로그 원고
    """
    
    # 시스템 프롬프트 가져오기
    system_prompt = get_system_prompt_v2()
    
    # 사용자 프롬프트 생성 (MongoDB 데이터 포함)
    user_prompt = generate_blog_content(
        keyword=keyword,
        ref=ref,
        min_length=1700,
        max_length=2000,
        note=note
    )
    
    print("=== 시스템 프롬프트 ===")
    print(system_prompt)
    print("\n" + "="*50 + "\n")
    
    print("=== 사용자 프롬프트 ===")
    print(user_prompt)
    print("\n" + "="*50 + "\n")
    
    # 실제 Claude API 호출은 여기서 수행
    # 현재는 프롬프트만 반환
    print("Claude API 호출을 위한 프롬프트가 준비되었습니다.")
    print("실제 원고 생성을 위해서는 Claude API를 호출해야 합니다.")
    
    return user_prompt


def manual_blog_creation():
    """
    수동으로 블로그 원고 작성 (Claude 프롬프트 기반)
    사용자가 직접 원고를 입력하여 저장
    """
    
    print("=== Claude 블로그 원고 생성기 ===")
    
    # 키워드 입력
    keyword = input("키워드를 입력하세요: ").strip()
    if not keyword:
        print("키워드가 입력되지 않았습니다.")
        return
    
    # 참조 문서 (선택사항)
    ref = input("참조 문서 (선택사항, Enter로 건너뛰기): ").strip()
    
    # 추가 요청사항 (선택사항)
    note = input("추가 요청사항 (선택사항, Enter로 건너뛰기): ").strip()
    
    # 프롬프트 생성
    prompt = create_blog_post(keyword, ref, note)
    
    print("\n" + "="*50)
    print("위 프롬프트를 Claude에게 전달하여 원고를 생성한 후,")
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


def demo_blog_creation():
    """
    데모용 블로그 원고 생성
    """
    keyword = "산업용 제습기"
    
    # 샘플 원고 (이전에 생성된 원고 사용)
    sample_content = """습도 관리의 중요성과 고민

요즘 공장이나 대형 사무실을 운영하시는 분들께서
습도 조절 때문에 많은 고민을 하고 계시죠
특히 장마철이나 겨울철처럼 외부 습도 변화가 클 때는
실내 환경 관리가 그야말로 골치 아픈 문제가 되더라구요
저도 40평 규모의 물류창고를 관리하면서 습도 문제로
정말 많은 시행착오를 겪었어요
제품 보관상태나 직원들의 작업 환경을 생각하면
무작정 넘길 수 없는 문제였거든요

산업용 제습기 조건과 가격 그리고 특징

산업용 제습기는 일반 가정용과는 차원이 다른
성능을 자랑하는 장비예요
하루 제습 용량이 50리터부터 300리터까지 다양하고
전력 소비량도 1.5kW에서 5kW까지 폭넓게 분포되어 있어요
가격대는 브랜드와 용량에 따라 200만원부터
800만원대까지 형성되어 있구요
제가 선택한 180리터급 모델은 약 420만원 정도였는데
40평 창고 기준으로는 적정 용량이라고 판단했답니다"""
    
    print("=== 데모: 블로그 원고 저장 ===")
    
    try:
        output_path = save_blog_content(sample_content, keyword, "output")
        print(f"데모 원고 저장 완료: {output_path}")
    except Exception as e:
        print(f"파일 저장 중 오류 발생: {e}")


def main():
    """메인 함수"""
    print("Claude 블로그 생성기")
    print("1. 수동 원고 생성 (프롬프트 + 수동 입력)")
    print("2. 데모 실행")
    print("3. 종료")
    
    choice = input("선택하세요 (1-3): ").strip()
    
    if choice == "1":
        manual_blog_creation()
    elif choice == "2":
        demo_blog_creation()
    elif choice == "3":
        print("종료합니다.")
    else:
        print("잘못된 선택입니다.")


if __name__ == "__main__":
    main()