# -*- coding: utf-8 -*-
"""
Step-by-Step PHASE 1-2 단계별 테스트 스크립트
각 단계를 하나씩 실행하면서 결과 확인
"""

import time
import json
from typing import Dict, Any, List
from llm.step_by.phase_functions import (
    phase_1_speaker_setting,
    phase_2_generate_subtitles,
    phase_3_generate_keywords,
    phase_4_generate_title,
    phase_5_generate_intro
)


class StepByStepTester:
    """단계별 테스트 클래스"""

    def __init__(self, keyword: str, reference: str = ""):
        self.keyword = keyword
        self.reference = reference
        self.results = {}
        self.start_time = time.time()

    def print_header(self, phase_num: int, phase_name: str):
        """단계 헤더 출력"""
        elapsed = time.time() - self.start_time
        print("\n" + "=" * 60)
        print(f"🔥 PHASE {phase_num}: {phase_name}")
        print(f"📝 키워드: {self.keyword}")
        print(f"⏱️ 경과시간: {elapsed:.1f}초")
        print("=" * 60)

    def print_result(self, phase_num: int, result: Any, show_full: bool = False):
        """단계 결과 출력"""
        print(f"\n✅ PHASE {phase_num} 완료!")
        print("📊 결과:")

        if isinstance(result, dict):
            for key, value in result.items():
                if isinstance(value, dict):
                    print(f"   🎭 {key}:")
                    for sub_key, sub_value in value.items():
                        print(f"      - {sub_key}: {sub_value}")
                elif isinstance(value, list):
                    print(f"   📋 {key}:")
                    for i, item in enumerate(value, 1):
                        print(f"      {i}. {item}")
                else:
                    print(f"   🏷️ {key}: {value}")
        elif isinstance(result, list):
            print("   📋 목록:")
            for i, item in enumerate(result, 1):
                print(f"      {i}. {item}")
        else:
            if show_full:
                print(f"   📄 전체 내용:")
                print("   " + "="*50)
                print("   " + str(result).replace("\n", "\n   "))
                print("   " + "="*50)
            else:
                preview = str(result)[:200] + "..." if len(str(result)) > 200 else str(result)
                print(f"   📄 내용: {preview}")
                if len(str(result)) > 200:
                    print(f"   💡 전체 내용을 보려면 show_full=True 옵션 사용")

    def test_phase_1(self, show_full: bool = False) -> Dict[str, Any]:
        """PHASE 1: 화자 설정 및 대분류 도출 테스트"""
        self.print_header(1, "화자 설정 및 대분류 도출")

        try:
            print("🚀 화자 설정 AI 호출 중...")
            result = phase_1_speaker_setting(self.keyword)

            self.results["phase1"] = result
            self.print_result(1, result, show_full)

            return result

        except Exception as e:
            print(f"❌ PHASE 1 실패: {e}")
            raise

    def test_phase_2(self, category: str) -> List[str]:
        """PHASE 2: 5개 독립 소제목 생성 테스트"""
        self.print_header(2, "5개 독립 소제목 생성")

        try:
            print("🚀 소제목 생성 AI 호출 중...")
            result = phase_2_generate_subtitles(self.keyword, category)

            self.results["phase2"] = result
            self.print_result(2, result)

            return result

        except Exception as e:
            print(f"❌ PHASE 2 실패: {e}")
            raise

    def test_phase_3(self, subtitles: List[str]) -> Dict[str, Any]:
        """PHASE 3: 연관키워드 40개 생성 테스트"""
        self.print_header(3, "연관키워드 40개 생성")

        try:
            print("🚀 연관키워드 생성 AI 호출 중...")
            result = phase_3_generate_keywords(self.keyword, subtitles)

            self.results["phase3"] = result
            self.print_result(3, result)

            return result

        except Exception as e:
            print(f"❌ PHASE 3 실패: {e}")
            raise

    def test_phase_4(self, subtitles: List[str], keywords: Dict[str, Any]) -> List[str]:
        """PHASE 4: 제목 생성 테스트"""
        self.print_header(4, "제목 생성")

        try:
            print("🚀 제목 생성 AI 호출 중...")
            result = phase_4_generate_title(self.keyword, subtitles, keywords)

            self.results["phase4"] = result
            self.print_result(4, result)

            return result

        except Exception as e:
            print(f"❌ PHASE 4 실패: {e}")
            raise

    def test_phase_5(self, speaker_info: Dict[str, Any]) -> str:
        """PHASE 5: 도입부 생성 테스트"""
        self.print_header(5, "도입부 생성 (200자)")

        try:
            print("🚀 도입부 생성 AI 호출 중...")
            result = phase_5_generate_intro(speaker_info, self.keyword)

            self.results["phase5"] = result
            self.print_result(5, result)

            return result

        except Exception as e:
            print(f"❌ PHASE 5 실패: {e}")
            raise

    def run_phases_1_to_2(self):
        """PHASE 1-2 실행"""
        print("🧪 PHASE 1-2 단계별 테스트 시작!")
        print(f"📝 키워드: {self.keyword}")
        print(f"📄 참조원고: {'있음' if self.reference else '없음'}")

        try:
            # PHASE 1: 화자 설정
            phase1_result = self.test_phase_1()
            category = phase1_result.get("category", "")

            # PHASE 2: 소제목 생성
            phase2_result = self.test_phase_2(category)

            print("\n" + "🎉" * 20)
            print("🎉 PHASE 1-2 테스트 완료!")
            print("🎉" * 20)

            return {
                "phase1": phase1_result,
                "phase2": phase2_result
            }

        except Exception as e:
            print(f"\n❌ 테스트 중단: {e}")
            raise

    def run_phases_1_to_3(self):
        """PHASE 1-3 실행"""
        print("🧪 PHASE 1-3 단계별 테스트 시작!")

        try:
            # PHASE 1-2 실행
            results_1_2 = self.run_phases_1_to_2()

            # PHASE 3: 연관키워드 생성
            phase3_result = self.test_phase_3(results_1_2["phase2"])

            print("\n" + "🎉" * 20)
            print("🎉 PHASE 1-3 테스트 완료!")
            print("🎉" * 20)

            return {
                **results_1_2,
                "phase3": phase3_result
            }

        except Exception as e:
            print(f"\n❌ 테스트 중단: {e}")
            raise

    def run_phases_1_to_4(self):
        """PHASE 1-4 실행"""
        print("🧪 PHASE 1-4 단계별 테스트 시작!")

        try:
            # PHASE 1-3 실행
            results_1_3 = self.run_phases_1_to_3()

            # PHASE 4: 제목 생성
            phase4_result = self.test_phase_4(
                results_1_3["phase2"],
                results_1_3["phase3"]
            )

            print("\n" + "🎉" * 20)
            print("🎉 PHASE 1-4 테스트 완료!")
            print("🎉" * 20)

            return {
                **results_1_3,
                "phase4": phase4_result
            }

        except Exception as e:
            print(f"\n❌ 테스트 중단: {e}")
            raise

    def run_phases_1_to_5(self):
        """PHASE 1-5 실행"""
        print("🧪 PHASE 1-5 단계별 테스트 시작!")

        try:
            # PHASE 1-4 실행
            results_1_4 = self.run_phases_1_to_4()

            # PHASE 5: 도입부 생성
            speaker_info = self.results["phase1"].get("speaker", {})
            phase5_result = self.test_phase_5(speaker_info)

            print("\n" + "🎉" * 20)
            print("🎉 PHASE 1-5 테스트 완료!")
            print("🎉" * 20)

            return {
                **results_1_4,
                "phase5": phase5_result
            }

        except Exception as e:
            print(f"\n❌ 테스트 중단: {e}")
            raise

    def print_final_summary(self):
        """최종 요약 출력"""
        total_time = time.time() - self.start_time

        print("\n" + "=" * 60)
        print("📊 최종 테스트 결과 요약")
        print("=" * 60)
        print(f"📝 키워드: {self.keyword}")
        print(f"⏱️ 총 소요시간: {total_time:.1f}초")
        print(f"✅ 완료된 단계: {len(self.results)}개")

        for phase, result in self.results.items():
            if isinstance(result, dict):
                print(f"   🔹 {phase}: {len(result)} 항목")
            elif isinstance(result, list):
                print(f"   🔹 {phase}: {len(result)} 개")
            else:
                print(f"   🔹 {phase}: 완료")

        print("=" * 60)


def test_specific_phases(keyword: str, max_phase: int = 2, reference: str = ""):
    """
    특정 단계까지만 테스트하는 함수

    Args:
        keyword: 테스트 키워드
        max_phase: 최대 실행할 단계 (1-5)
        reference: 참조 원고
    """
    tester = StepByStepTester(keyword, reference)

    try:
        if max_phase == 1:
            result = tester.test_phase_1()
        elif max_phase == 2:
            result = tester.run_phases_1_to_2()
        elif max_phase == 3:
            result = tester.run_phases_1_to_3()
        elif max_phase == 4:
            result = tester.run_phases_1_to_4()
        elif max_phase == 5:
            result = tester.run_phases_1_to_5()
        else:
            raise ValueError(f"지원하지 않는 단계: {max_phase}")

        tester.print_final_summary()
        return result

    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        tester.print_final_summary()
        raise


def test_with_full_output(keyword: str, max_phase: int = 2, reference: str = ""):
    """
    전체 AI 응답을 출력하면서 테스트하는 함수

    Args:
        keyword: 테스트 키워드
        max_phase: 최대 실행할 단계 (1-5)
        reference: 참조 원고
    """
    print("🔍" * 30)
    print("🔍 FULL OUTPUT 모드 테스트")
    print(f"🔍 키워드: {keyword}")
    print(f"🔍 최대 단계: PHASE {max_phase}")
    print("🔍" * 30)

    tester = StepByStepTester(keyword, reference)

    try:
        if max_phase >= 1:
            print("\n📄 PHASE 1 - 전체 AI 응답 출력")
            result1 = tester.test_phase_1(show_full=True)
            category = result1.get("category", "")

        if max_phase >= 2:
            print("\n📄 PHASE 2 - 전체 AI 응답 출력")
            result2 = tester.test_phase_2(category)
            tester.print_result(2, result2, show_full=True)

        if max_phase >= 3:
            print("\n📄 PHASE 3 - 전체 AI 응답 출력")
            result3 = tester.test_phase_3(result2)
            tester.print_result(3, result3, show_full=True)

        if max_phase >= 4:
            print("\n📄 PHASE 4 - 전체 AI 응답 출력")
            result4 = tester.test_phase_4(result2, result3)
            tester.print_result(4, result4, show_full=True)

        if max_phase >= 5:
            print("\n📄 PHASE 5 - 전체 AI 응답 출력")
            speaker_info = result1.get("speaker", {})
            result5 = tester.test_phase_5(speaker_info)
            tester.print_result(5, result5, show_full=True)

        tester.print_final_summary()

        return tester.results

    except Exception as e:
        print(f"❌ 전체 출력 테스트 실패: {e}")
        tester.print_final_summary()
        raise


if __name__ == "__main__":
    # 기본 테스트 선택
    test_keyword = "위고비 가격"

    print("🎮 테스트 모드 선택:")
    print("1️⃣ 기본 테스트 (요약 출력)")
    print("2️⃣ 전체 출력 테스트 (AI 응답 전체)")
    print("3️⃣ 상세 verbose 테스트 (프롬프트+응답 전체)")

    try:
        choice = input("선택하세요 (1, 2, 3): ").strip()

        if choice == "1":
            print("🔬 PHASE 1-2 기본 테스트 실행!")
            result = test_specific_phases(test_keyword, max_phase=2)

        elif choice == "2":
            print("🔍 PHASE 1-2 전체 출력 테스트 실행!")
            result = test_with_full_output(test_keyword, max_phase=2)

        elif choice == "3":
            print("📄 PHASE 1-2 상세 verbose 테스트 실행!")
            from test_phase_verbose import verbose_test_phases
            result = verbose_test_phases(test_keyword, max_phase=2)

        else:
            print("❌ 잘못된 선택, 기본 테스트 실행")
            result = test_specific_phases(test_keyword, max_phase=2)

    except KeyboardInterrupt:
        print("\n👋 테스트 중단!")
    except Exception as e:
        print(f"❌ 테스트 오류: {e}")

    print("\n" + "="*60)
    print("💡 다른 단계 테스트 방법:")
    print("   test_specific_phases('키워드', max_phase=1)     # PHASE 1만")
    print("   test_with_full_output('키워드', max_phase=3)    # PHASE 1-3 전체 출력")
    print("   verbose_test_phases('키워드', max_phase=4)      # PHASE 1-4 상세")