# -*- coding: utf-8 -*-
"""
Step-by-Step PHASE 대화형 테스트 스크립트
사용자가 단계별로 진행하면서 결과 확인
"""

import time
import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from test_phase_step_by_step import StepByStepTester


class InteractiveStepTester:
    """대화형 단계별 테스트 클래스"""

    def __init__(self, keyword: str, reference: str = ""):
        self.keyword = keyword
        self.reference = reference
        self.tester = StepByStepTester(keyword, reference)
        self.current_phase = 0
        self.test_session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.results_dir = "test_results"
        self._create_results_dir()

    def _create_results_dir(self):
        """결과 저장 디렉토리 생성"""
        if not os.path.exists(self.results_dir):
            os.makedirs(self.results_dir)

    def save_phase_result(self, phase_num: int, result: Any):
        """단계 결과 저장"""
        filename = f"{self.results_dir}/phase_{phase_num}_{self.test_session_id}.json"

        result_data = {
            "keyword": self.keyword,
            "reference": self.reference,
            "phase": phase_num,
            "timestamp": datetime.now().isoformat(),
            "result": result
        }

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(result_data, f, ensure_ascii=False, indent=2)

            print(f"💾 결과 저장: {filename}")

        except Exception as e:
            print(f"⚠️ 결과 저장 실패: {e}")

    def load_phase_result(self, phase_num: int) -> Optional[Any]:
        """이전 단계 결과 불러오기"""
        filename = f"{self.results_dir}/phase_{phase_num}_{self.test_session_id}.json"

        try:
            if os.path.exists(filename):
                with open(filename, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return data["result"]
            return None

        except Exception as e:
            print(f"⚠️ 결과 로드 실패: {e}")
            return None

    def show_menu(self):
        """메뉴 표시"""
        print("\n" + "🎮" * 20)
        print("🎮 Step-by-Step 대화형 테스트")
        print("🎮" * 20)
        print(f"📝 키워드: {self.keyword}")
        print(f"📊 현재 단계: PHASE {self.current_phase}")
        print()
        print("📋 메뉴:")
        print("   1️⃣ PHASE 1 실행 (화자 설정)")
        print("   2️⃣ PHASE 2 실행 (소제목 생성)")
        print("   3️⃣ PHASE 3 실행 (연관키워드)")
        print("   4️⃣ PHASE 4 실행 (제목 생성)")
        print("   5️⃣ PHASE 5 실행 (도입부 생성)")
        print()
        print("   🔄 r - 이전 결과 확인")
        print("   📊 s - 전체 요약 보기")
        print("   💾 d - 결과 파일 다운로드 위치")
        print("   ❌ q - 종료")
        print("="*40)

    def show_previous_results(self):
        """이전 결과들 요약 표시"""
        print("\n📊 이전 단계 결과 요약:")
        print("="*40)

        for phase in range(1, 6):
            result = self.load_phase_result(phase)
            if result:
                print(f"✅ PHASE {phase}: 완료")
                if isinstance(result, dict):
                    print(f"   📋 항목 수: {len(result)}")
                elif isinstance(result, list):
                    print(f"   📋 목록 수: {len(result)}")
                else:
                    print(f"   📋 결과 있음")
            else:
                print(f"⏸️ PHASE {phase}: 미실행")

        print("="*40)

    def run_phase_with_deps(self, target_phase: int):
        """의존성 체크하면서 단계 실행"""
        print(f"\n🚀 PHASE {target_phase} 실행 준비...")

        # 의존성 체크 및 자동 실행
        if target_phase >= 2:
            phase1_result = self.load_phase_result(1)
            if not phase1_result:
                print("⚠️ PHASE 1 결과가 없습니다. 먼저 PHASE 1을 실행합니다.")
                self.run_single_phase(1)
                phase1_result = self.load_phase_result(1)

        if target_phase >= 3:
            phase2_result = self.load_phase_result(2)
            if not phase2_result:
                print("⚠️ PHASE 2 결과가 없습니다. 먼저 PHASE 2를 실행합니다.")
                self.run_single_phase(2)

        if target_phase >= 4:
            phase3_result = self.load_phase_result(3)
            if not phase3_result:
                print("⚠️ PHASE 3 결과가 없습니다. 먼저 PHASE 3을 실행합니다.")
                self.run_single_phase(3)

        if target_phase >= 5:
            phase4_result = self.load_phase_result(4)
            if not phase4_result:
                print("⚠️ PHASE 4 결과가 없습니다. 먼저 PHASE 4를 실행합니다.")
                self.run_single_phase(4)

        # 목표 단계 실행
        self.run_single_phase(target_phase)

    def run_single_phase(self, phase_num: int):
        """단일 단계 실행"""
        try:
            if phase_num == 1:
                result = self.tester.test_phase_1()

            elif phase_num == 2:
                phase1_result = self.load_phase_result(1)
                category = phase1_result.get("category", "")
                result = self.tester.test_phase_2(category)

            elif phase_num == 3:
                phase2_result = self.load_phase_result(2)
                result = self.tester.test_phase_3(phase2_result)

            elif phase_num == 4:
                phase2_result = self.load_phase_result(2)
                phase3_result = self.load_phase_result(3)
                result = self.tester.test_phase_4(phase2_result, phase3_result)

            elif phase_num == 5:
                phase1_result = self.load_phase_result(1)
                speaker_info = phase1_result.get("speaker", {})
                result = self.tester.test_phase_5(speaker_info)

            else:
                print(f"❌ 지원하지 않는 단계: {phase_num}")
                return

            # 결과 저장
            self.save_phase_result(phase_num, result)
            self.current_phase = max(self.current_phase, phase_num)

            print(f"\n✅ PHASE {phase_num} 완료!")

        except Exception as e:
            print(f"❌ PHASE {phase_num} 실행 실패: {e}")

    def show_download_info(self):
        """다운로드 정보 표시"""
        print(f"\n💾 결과 파일 저장 위치:")
        print(f"📁 폴더: {os.path.abspath(self.results_dir)}/")
        print(f"🏷️ 세션 ID: {self.test_session_id}")
        print()
        print("📋 저장된 파일들:")

        for phase in range(1, 6):
            filename = f"phase_{phase}_{self.test_session_id}.json"
            filepath = os.path.join(self.results_dir, filename)
            if os.path.exists(filepath):
                file_size = os.path.getsize(filepath)
                print(f"   ✅ {filename} ({file_size:,} bytes)")
            else:
                print(f"   ⏸️ {filename} (미생성)")

    def run_interactive(self):
        """대화형 실행"""
        print("🎮 Step-by-Step 대화형 테스트 시작!")

        while True:
            self.show_menu()

            try:
                choice = input("🎯 선택하세요: ").strip().lower()

                if choice == 'q':
                    print("👋 테스트 종료!")
                    break

                elif choice in ['1', '2', '3', '4', '5']:
                    phase_num = int(choice)
                    self.run_phase_with_deps(phase_num)

                elif choice == 'r':
                    self.show_previous_results()

                elif choice == 's':
                    self.tester.print_final_summary()

                elif choice == 'd':
                    self.show_download_info()

                else:
                    print("❌ 잘못된 선택입니다.")

            except KeyboardInterrupt:
                print("\n\n👋 테스트 중단!")
                break

            except Exception as e:
                print(f"❌ 오류 발생: {e}")

            # 계속하기 전 잠시 대기
            input("\n⏸️ 계속하려면 Enter를 누르세요...")


def quick_test(keyword: str, phases: List[int]):
    """빠른 연속 테스트"""
    print(f"⚡ 빠른 테스트: PHASE {'-'.join(map(str, phases))}")

    tester = InteractiveStepTester(keyword)

    for phase in sorted(phases):
        print(f"\n🔥 PHASE {phase} 실행 중...")
        tester.run_phase_with_deps(phase)

    print("\n🎉 빠른 테스트 완료!")
    tester.show_download_info()


if __name__ == "__main__":
    # 기본 키워드
    test_keyword = "위고비 가격"

    print("🎮 대화형 테스트 vs ⚡ 빠른 테스트")
    print("1️⃣ 대화형 테스트 (단계별 진행)")
    print("2️⃣ 빠른 테스트 (PHASE 1-2 연속)")

    choice = input("선택하세요 (1 또는 2): ").strip()

    if choice == "1":
        # 대화형 테스트
        tester = InteractiveStepTester(test_keyword)
        tester.run_interactive()

    elif choice == "2":
        # 빠른 테스트 (PHASE 1-2)
        quick_test(test_keyword, [1, 2])

    else:
        print("❌ 잘못된 선택")