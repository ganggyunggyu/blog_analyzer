# -*- coding: utf-8 -*-
"""
Step-by-Step PHASE별 상세 AI 응답 확인 테스트
각 단계의 AI 응답을 완전히 출력하여 디버깅 및 검증
"""

import time
import json
from typing import Dict, Any, List
from llm.step_by.phase_functions import (
    phase_1_speaker_setting,
    phase_2_generate_subtitles,
    phase_3_generate_keywords,
    phase_4_generate_title,
    phase_5_generate_intro,
    call_openai_with_prompt
)


class VerboseStepByStepTester:
    """상세 출력 단계별 테스트 클래스"""

    def __init__(self, keyword: str, reference: str = ""):
        self.keyword = keyword
        self.reference = reference
        self.results = {}
        self.start_time = time.time()
        self.verbose = True  # 상세 출력 모드

    def print_phase_header(self, phase_num: int, phase_name: str):
        """단계 헤더 출력"""
        print("\n" + "🔥" * 60)
        print(f"🔥 PHASE {phase_num}: {phase_name}")
        print(f"📝 키워드: {self.keyword}")
        print(f"⏱️ 시작 시간: {time.strftime('%H:%M:%S')}")
        print("🔥" * 60)

    def print_ai_response_full(self, phase_num: int, raw_response: str, parsed_result: Any):
        """AI 응답 전체 출력"""
        print("\n" + "📄" * 40)
        print(f"📄 PHASE {phase_num} - AI 원본 응답")
        print("📄" * 40)
        print(raw_response)
        print("📄" * 40)

        print("\n" + "🔍" * 40)
        print(f"🔍 PHASE {phase_num} - 파싱된 결과")
        print("🔍" * 40)

        if isinstance(parsed_result, dict):
            print(json.dumps(parsed_result, ensure_ascii=False, indent=2))
        elif isinstance(parsed_result, list):
            for i, item in enumerate(parsed_result, 1):
                print(f"{i:2d}. {item}")
        else:
            print(parsed_result)

        print("🔍" * 40)

    def test_phase_1_verbose(self) -> Dict[str, Any]:
        """PHASE 1: 화자 설정 상세 테스트"""
        self.print_phase_header(1, "화자 설정 및 대분류 도출")

        try:
            # 프롬프트 확인
            from llm.step_by.prompts import STEP_BY_STEP_PROMPTS
            prompt = STEP_BY_STEP_PROMPTS["phase_1_speaker_setting"].format(keyword=self.keyword)

            print("📝 전송할 프롬프트:")
            print("=" * 50)
            print(prompt)
            print("=" * 50)

            # AI 호출
            print("\n🤖 AI 호출 중...")
            raw_response = call_openai_with_prompt(prompt)

            # 응답 파싱
            from llm.step_by.phase_functions import parse_json_response
            parsed_result = parse_json_response(raw_response)

            # 전체 응답 출력
            self.print_ai_response_full(1, raw_response, parsed_result)

            self.results["phase1"] = {
                "prompt": prompt,
                "raw_response": raw_response,
                "parsed_result": parsed_result
            }

            return parsed_result

        except Exception as e:
            print(f"❌ PHASE 1 실패: {e}")
            raise

    def test_phase_2_verbose(self, category: str) -> List[str]:
        """PHASE 2: 소제목 생성 상세 테스트"""
        self.print_phase_header(2, "5개 독립 소제목 생성")

        try:
            # 프롬프트 확인
            from llm.step_by.prompts import STEP_BY_STEP_PROMPTS
            prompt = STEP_BY_STEP_PROMPTS["phase_2_subtitles"].format(
                keyword=self.keyword,
                category=category
            )

            print("📝 전송할 프롬프트:")
            print("=" * 50)
            print(prompt)
            print("=" * 50)

            # AI 호출
            print("\n🤖 AI 호출 중...")
            raw_response = call_openai_with_prompt(prompt)

            # 응답 파싱
            from llm.step_by.phase_functions import parse_json_response
            parsed_result = parse_json_response(raw_response)
            subtitles = parsed_result.get("subtitles", []) if isinstance(parsed_result, dict) else []

            # 전체 응답 출력
            self.print_ai_response_full(2, raw_response, subtitles)

            self.results["phase2"] = {
                "prompt": prompt,
                "raw_response": raw_response,
                "parsed_result": parsed_result,
                "subtitles": subtitles
            }

            return subtitles

        except Exception as e:
            print(f"❌ PHASE 2 실패: {e}")
            raise

    def test_phase_3_verbose(self, subtitles: List[str]) -> Dict[str, Any]:
        """PHASE 3: 연관키워드 생성 상세 테스트"""
        self.print_phase_header(3, "연관키워드 40개 생성")

        try:
            # 프롬프트 확인
            from llm.step_by.prompts import STEP_BY_STEP_PROMPTS
            subtitles_text = "\n".join([f"{i+1}. {subtitle}" for i, subtitle in enumerate(subtitles)])
            prompt = STEP_BY_STEP_PROMPTS["phase_3_keywords"].format(
                keyword=self.keyword,
                subtitles=subtitles_text
            )

            print("📝 전송할 프롬프트:")
            print("=" * 50)
            print(prompt)
            print("=" * 50)

            # AI 호출
            print("\n🤖 AI 호출 중...")
            raw_response = call_openai_with_prompt(prompt)

            # 응답 파싱
            from llm.step_by.phase_functions import parse_json_response
            parsed_result = parse_json_response(raw_response)

            # 전체 응답 출력
            self.print_ai_response_full(3, raw_response, parsed_result)

            self.results["phase3"] = {
                "prompt": prompt,
                "raw_response": raw_response,
                "parsed_result": parsed_result
            }

            return parsed_result

        except Exception as e:
            print(f"❌ PHASE 3 실패: {e}")
            raise

    def test_phase_4_verbose(self, subtitles: List[str], keywords: Dict[str, Any]) -> List[str]:
        """PHASE 4: 제목 생성 상세 테스트"""
        self.print_phase_header(4, "제목 생성")

        try:
            # 프롬프트 확인
            from llm.step_by.prompts import STEP_BY_STEP_PROMPTS
            subtitles_text = "\n".join([f"{i+1}. {subtitle}" for i, subtitle in enumerate(subtitles)])
            keywords_text = json.dumps(keywords, ensure_ascii=False, indent=2)

            prompt = STEP_BY_STEP_PROMPTS["phase_4_title"].format(
                keyword=self.keyword,
                subtitles=subtitles_text,
                keywords=keywords_text
            )

            print("📝 전송할 프롬프트:")
            print("=" * 50)
            print(prompt)
            print("=" * 50)

            # AI 호출
            print("\n🤖 AI 호출 중...")
            raw_response = call_openai_with_prompt(prompt)

            # 응답 파싱
            from llm.step_by.phase_functions import parse_json_response
            parsed_result = parse_json_response(raw_response)
            titles = parsed_result.get("titles", []) if isinstance(parsed_result, dict) else []

            # 전체 응답 출력
            self.print_ai_response_full(4, raw_response, titles)

            self.results["phase4"] = {
                "prompt": prompt,
                "raw_response": raw_response,
                "parsed_result": parsed_result,
                "titles": titles
            }

            return titles

        except Exception as e:
            print(f"❌ PHASE 4 실패: {e}")
            raise

    def test_phase_5_verbose(self, speaker_info: Dict[str, Any]) -> str:
        """PHASE 5: 도입부 생성 상세 테스트"""
        self.print_phase_header(5, "도입부 생성 (200자)")

        try:
            # 프롬프트 확인
            from llm.step_by.prompts import STEP_BY_STEP_PROMPTS
            speaker_text = json.dumps(speaker_info, ensure_ascii=False, indent=2)

            prompt = STEP_BY_STEP_PROMPTS["phase_5_intro"].format(
                keyword=self.keyword,
                speaker_info=speaker_text
            )

            print("📝 전송할 프롬프트:")
            print("=" * 50)
            print(prompt)
            print("=" * 50)

            # AI 호출
            print("\n🤖 AI 호출 중...")
            raw_response = call_openai_with_prompt(prompt)

            # 텍스트 클리닝
            from utils.text_cleaner import comprehensive_text_clean
            cleaned_intro = comprehensive_text_clean(raw_response)

            # 전체 응답 출력
            self.print_ai_response_full(5, raw_response, cleaned_intro)

            self.results["phase5"] = {
                "prompt": prompt,
                "raw_response": raw_response,
                "cleaned_result": cleaned_intro
            }

            return cleaned_intro

        except Exception as e:
            print(f"❌ PHASE 5 실패: {e}")
            raise

    def run_verbose_test(self, max_phase: int = 2):
        """상세 출력 테스트 실행"""
        print("🔬" * 30)
        print("🔬 Step-by-Step 상세 AI 응답 테스트")
        print(f"🔬 키워드: {self.keyword}")
        print(f"🔬 최대 단계: PHASE {max_phase}")
        print("🔬" * 30)

        try:
            results = {}

            # PHASE 1
            if max_phase >= 1:
                phase1_result = self.test_phase_1_verbose()
                results["phase1"] = phase1_result
                category = phase1_result.get("category", "")

            # PHASE 2
            if max_phase >= 2:
                phase2_result = self.test_phase_2_verbose(category)
                results["phase2"] = phase2_result

            # PHASE 3
            if max_phase >= 3:
                phase3_result = self.test_phase_3_verbose(results["phase2"])
                results["phase3"] = phase3_result

            # PHASE 4
            if max_phase >= 4:
                phase4_result = self.test_phase_4_verbose(
                    results["phase2"],
                    results["phase3"]
                )
                results["phase4"] = phase4_result

            # PHASE 5
            if max_phase >= 5:
                speaker_info = results["phase1"].get("speaker", {})
                phase5_result = self.test_phase_5_verbose(speaker_info)
                results["phase5"] = phase5_result

            self.print_final_verbose_summary(max_phase)
            return results

        except Exception as e:
            print(f"❌ 상세 테스트 실패: {e}")
            raise

    def print_final_verbose_summary(self, max_phase: int):
        """최종 상세 요약"""
        total_time = time.time() - self.start_time

        print("\n" + "🎉" * 50)
        print("🎉 상세 AI 응답 테스트 완료!")
        print("🎉" * 50)
        print(f"📝 키워드: {self.keyword}")
        print(f"⏱️ 총 소요시간: {total_time:.1f}초")
        print(f"✅ 완료된 단계: PHASE 1-{max_phase}")

        print(f"\n📊 각 단계별 응답 요약:")
        for phase_key, phase_data in self.results.items():
            if isinstance(phase_data, dict) and "raw_response" in phase_data:
                response_length = len(phase_data["raw_response"])
                print(f"   🔹 {phase_key}: {response_length:,}자 응답")

        print("🎉" * 50)

    def save_verbose_results(self, filename: str = None):
        """상세 결과 저장"""
        if not filename:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"verbose_test_results_{timestamp}.json"

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, ensure_ascii=False, indent=2)

            print(f"💾 상세 결과 저장: {filename}")
            return filename

        except Exception as e:
            print(f"⚠️ 결과 저장 실패: {e}")
            return None


def verbose_test_phases(keyword: str, max_phase: int = 2, save_results: bool = True):
    """
    상세 출력 단계별 테스트 함수

    Args:
        keyword: 테스트 키워드
        max_phase: 최대 실행할 단계
        save_results: 결과 저장 여부
    """
    tester = VerboseStepByStepTester(keyword)

    try:
        results = tester.run_verbose_test(max_phase)

        if save_results:
            tester.save_verbose_results()

        return results

    except Exception as e:
        print(f"❌ 상세 테스트 실패: {e}")
        raise


if __name__ == "__main__":
    # 기본 테스트: PHASE 1-2 상세 출력
    test_keyword = "위고비 가격"

    print("🔬 PHASE 1-2 상세 AI 응답 테스트!")

    # 상세 테스트 실행
    results = verbose_test_phases(test_keyword, max_phase=2)

    print("\n" + "="*60)
    print("💡 다른 단계 상세 테스트:")
    print("   verbose_test_phases('키워드', max_phase=1)  # PHASE 1만 상세")
    print("   verbose_test_phases('키워드', max_phase=3)  # PHASE 1-3 상세")
    print("   verbose_test_phases('키워드', max_phase=4)  # PHASE 1-4 상세")
    print("   verbose_test_phases('키워드', max_phase=5)  # PHASE 1-5 상세")