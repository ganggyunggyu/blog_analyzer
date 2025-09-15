# -*- coding: utf-8 -*-
"""
Step-by-Step PHASE 1만 테스트하는 스크립트
화자 설정 및 대분류 도출 단계만 실행하여 결과 확인
"""

import time
from llm.step_by.phase_functions import phase_1_speaker_setting


def test_phase_1_only(keyword: str):
    """
    PHASE 1: 화자 설정 및 대분류 도출만 테스트

    Args:
        keyword: 테스트할 키워드

    Returns:
        PHASE 1 결과
    """
    print("=" * 60)
    print("🔥 PHASE 1 테스트 시작!")
    print(f"📝 키워드: {keyword}")
    print("=" * 60)

    start_time = time.time()

    try:
        # PHASE 1: 화자 설정 실행
        print("\n🚀 PHASE 1: 화자 설정 및 대분류 도출 실행 중...")

        phase1_result = phase_1_speaker_setting(keyword)

        # 결과 출력
        elapsed_time = time.time() - start_time

        print("\n✅ PHASE 1 완료!")
        print(f"⏱️ 소요시간: {elapsed_time:.2f}초")
        print("=" * 60)

        # 결과 상세 출력
        print("📊 PHASE 1 결과:")
        print(f"🎭 화자 정보: {phase1_result.get('speaker', {})}")
        print(f"📂 카테고리: {phase1_result.get('category', 'N/A')}")
        print("=" * 60)

        return phase1_result

    except Exception as e:
        print(f"❌ PHASE 1 테스트 실패: {e}")
        raise


def main():
    """메인 테스트 실행"""

    # 테스트할 키워드들
    test_keywords = [
        "위고비 가격",
        "다이어트 방법",
        "파이썬 프로그래밍",
        "블로그 운영"
    ]

    print("🧪 PHASE 1 단독 테스트 시작!")
    print(f"📋 테스트 키워드 {len(test_keywords)}개")
    print("=" * 60)

    for i, keyword in enumerate(test_keywords, 1):
        try:
            print(f"\n🔍 테스트 {i}/{len(test_keywords)}")
            result = test_phase_1_only(keyword)

            # 간단한 검증
            if "speaker" in result and "category" in result:
                print("✅ 결과 검증 통과")
            else:
                print("⚠️ 결과 검증 실패 - 필수 키가 없음")

        except Exception as e:
            print(f"❌ 키워드 '{keyword}' 테스트 실패: {e}")

        # 다음 테스트를 위한 대기
        if i < len(test_keywords):
            print("\n⏳ 2초 대기 중...")
            time.sleep(2)

    print("\n🎉 모든 PHASE 1 테스트 완료!")


if __name__ == "__main__":
    # 단일 키워드 테스트
    single_keyword = "위고비 가격"
    print("🔬 단일 키워드 테스트")

    try:
        result = test_phase_1_only(single_keyword)
        print("\n✨ 최종 결과:")
        print(result)

    except Exception as e:
        print(f"❌ 테스트 실패: {e}")

    print("\n" + "="*60)
    print("💡 다중 키워드 테스트를 원하면 main() 함수를 실행하세요!")

    # 사용자가 원하면 다중 테스트도 실행
    # main()