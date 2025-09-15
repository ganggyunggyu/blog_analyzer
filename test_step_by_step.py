# -*- coding: utf-8 -*-
"""
스텝바이스텝 원고 생성 테스트 스크립트
"""

import time
import sys
import os

# 프로젝트 루트를 파이썬 패스에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from llm.step_by import step_by_step_generate, step_by_step_generate_detailed


def test_simple_generation():
    """간단한 원고 생성 테스트"""
    print("🚀 스텝바이스텝 간단 테스트 시작!")
    print("=" * 60)

    keyword = "위고비 가격"
    reference = """
    다이어트 주사로 유명한 위고비는 많은 사람들이 관심을 가지고 있습니다.
    비급여 항목이라 병원마다 가격이 다를 수 있어요.
    효과는 좋지만 부작용도 있으니 전문의와 상담이 필요합니다.
    """

    try:
        start_time = time.time()

        # 스텝바이스텝 원고 생성
        generated_text = step_by_step_generate(
            keyword=keyword,
            reference=reference
        )

        end_time = time.time()

        print(f"\n✅ 테스트 완료!")
        print(f"⏱️ 소요시간: {end_time - start_time:.1f}초")
        print(f"📊 생성 글자수: {len(generated_text.replace(' ', ''))}자")
        print(f"📊 생성 문자수: {len(generated_text)}자")

        print("\n" + "=" * 60)
        print("📝 생성된 원고:")
        print("=" * 60)
        print(generated_text)
        print("=" * 60)

        return True

    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        return False


def test_detailed_generation():
    """상세 결과 포함 원고 생성 테스트"""
    print("\n🔍 스텝바이스텝 상세 테스트 시작!")
    print("=" * 60)

    keyword = "마운자로 부작용"

    try:
        start_time = time.time()

        # 상세 결과 포함 원고 생성
        detailed_result = step_by_step_generate_detailed(
            keyword=keyword,
            reference=""
        )

        end_time = time.time()

        print(f"\n✅ 상세 테스트 완료!")
        print(f"⏱️ 소요시간: {end_time - start_time:.1f}초")

        # 결과 출력
        print(f"\n📝 제목: {detailed_result.get('title', 'N/A')}")
        print(f"📊 생성 글자수: {detailed_result.get('word_count', 0)}자")
        print(f"🎭 카테고리: {detailed_result.get('category', 'N/A')}")

        print(f"\n📋 소제목 목록:")
        for i, subtitle in enumerate(detailed_result.get('subtitles', []), 1):
            print(f"   {i}. {subtitle}")

        print(f"\n🔍 키워드 사용 현황:")
        for word, count in detailed_result.get('keyword_count', {}).items():
            status = "✅" if count <= 5 else "⚠️"
            print(f"   {status} {word}: {count}회")

        print(f"\n🎭 화자 정보:")
        speaker_info = detailed_result.get('speaker_info', {})
        for key, value in speaker_info.items():
            print(f"   {key}: {value}")

        return True

    except Exception as e:
        print(f"❌ 상세 테스트 실패: {e}")
        return False


def test_api_simulation():
    """API 시뮬레이션 테스트"""
    print("\n🌐 API 시뮬레이션 테스트 시작!")
    print("=" * 60)

    # 테스트 케이스들
    test_cases = [
        {"keyword": "삭센다 효과", "ref": ""},
        {"keyword": "GLP-1 주사 종류", "ref": "다이어트 주사에는 여러 종류가 있습니다."},
        {"keyword": "체중감량 주사 비교", "ref": ""}
    ]

    success_count = 0

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 테스트 케이스 {i}/{len(test_cases)}")
        print(f"   키워드: {test_case['keyword']}")
        print(f"   참조원고: {'있음' if test_case['ref'] else '없음'}")

        try:
            start_time = time.time()

            # 원고 생성
            result = step_by_step_generate(
                keyword=test_case['keyword'],
                reference=test_case['ref']
            )

            end_time = time.time()

            if result and len(result) > 100:  # 최소 100자 이상
                print(f"   ✅ 성공 ({end_time - start_time:.1f}초, {len(result)}자)")
                success_count += 1
            else:
                print(f"   ❌ 실패 (결과 부족)")

        except Exception as e:
            print(f"   ❌ 실패: {e}")

        time.sleep(2)  # API 호출 간격

    print(f"\n📊 테스트 결과: {success_count}/{len(test_cases)} 성공")
    return success_count == len(test_cases)


def main():
    """메인 테스트 함수"""
    print("🧪 스텝바이스텝 원고 생성 종합 테스트")
    print("=" * 60)

    # 환경 체크
    from config import OPENAI_API_KEY
    if not OPENAI_API_KEY:
        print("❌ OPENAI_API_KEY가 설정되지 않았습니다!")
        return False

    print("✅ 환경 설정 확인 완료")

    all_passed = True

    # 테스트 1: 간단한 생성
    if not test_simple_generation():
        all_passed = False

    # 테스트 2: 상세 생성
    if not test_detailed_generation():
        all_passed = False

    # 테스트 3: API 시뮬레이션
    if not test_api_simulation():
        all_passed = False

    # 최종 결과
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 모든 테스트 통과!")
        print("✅ 스텝바이스텝 시스템이 정상 작동합니다.")
    else:
        print("❌ 일부 테스트 실패!")
        print("⚠️ 시스템을 점검해주세요.")

    print("=" * 60)
    return all_passed


if __name__ == "__main__":
    main()