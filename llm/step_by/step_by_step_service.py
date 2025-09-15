# -*- coding: utf-8 -*-
"""
스텝바이스텝 원고 생성 통합 서비스
10단계 PHASE를 순차적으로 실행하여 완성된 원고 생성
"""

import time
from typing import Dict, Any, List, Optional

from utils.text_cleaner import comprehensive_text_clean
from utils.format_paragraphs import format_paragraphs
from .phase_functions import (
    phase_1_speaker_setting,
    phase_2_generate_subtitles,
    phase_3_generate_keywords,
    phase_4_generate_title,
    phase_5_generate_intro,
    phase_6_generate_content,
    phase_7_generate_conclusion,
    phase_8_keyword_check
)


class StepByStepManuscriptGenerator:
    """스텝바이스텝 원고 생성기 클래스"""

    def __init__(self):
        self.results = {}
        self.start_time = None
        self.current_phase = 0
        self.total_phases = 8

    def generate_manuscript(self, keyword: str, reference: str = "") -> Dict[str, Any]:
        """
        전체 스텝바이스텝 원고 생성 프로세스

        Args:
            keyword: 메인 키워드
            reference: 참조 원고 (선택적)

        Returns:
            완성된 원고와 모든 단계별 결과
        """
        self.start_time = time.time()
        self.results = {"keyword": keyword, "reference": reference}

        print(f"🚀 스텝바이스텝 원고 생성 시작!")
        print(f"📝 키워드: {keyword}")
        print(f"📄 참조원고: {'있음' if reference else '없음'}")
        print("=" * 60)

        try:
            # PHASE 1: 화자 설정
            self._next_phase("화자 설정 및 대분류 도출")
            phase1_result = phase_1_speaker_setting(keyword)
            self.results["phase1_speaker"] = phase1_result

            category = phase1_result.get("category", "")
            speaker_info = phase1_result.get("speaker", {})

            # PHASE 2: 소제목 생성
            self._next_phase("5개 독립 소제목 생성")
            subtitles = phase_2_generate_subtitles(keyword, category)
            self.results["phase2_subtitles"] = subtitles

            # PHASE 3: 연관키워드 생성
            self._next_phase("연관키워드 40개 생성")
            keywords = phase_3_generate_keywords(keyword, subtitles)
            self.results["phase3_keywords"] = keywords

            # PHASE 4: 제목 생성
            self._next_phase("제목 생성")
            titles = phase_4_generate_title(keyword, subtitles, keywords)
            self.results["phase4_titles"] = titles
            final_title = titles[0] if titles else f"{keyword} 완벽 가이드"

            # PHASE 5: 도입부 생성
            self._next_phase("도입부 생성")
            intro = phase_5_generate_intro(speaker_info, keyword)
            self.results["phase5_intro"] = intro

            # PHASE 6: 각 소제목별 본문 생성
            self._next_phase("본문 생성 (5개 소제목)")
            contents = []
            for i, subtitle in enumerate(subtitles, 1):
                print(f"   📝 소제목 {i}/5: {subtitle}")
                content = phase_6_generate_content(subtitle, speaker_info, keywords, reference)
                contents.append({
                    "subtitle": subtitle,
                    "content": content
                })
                time.sleep(1)  # API 호출 간격

            self.results["phase6_contents"] = contents

            # PHASE 7: 마무리 생성
            self._next_phase("마무리 생성")
            content_summary = self._create_content_summary(contents)
            conclusion = phase_7_generate_conclusion(speaker_info, keyword, content_summary)
            self.results["phase7_conclusion"] = conclusion

            # 전체 원고 조합
            full_content = self._assemble_full_content(final_title, intro, contents, conclusion)

            # PHASE 8: 키워드 반복 체크 및 수정 (임시 스킵)
            self._next_phase("키워드 반복 체크 및 수정")
            print("⚠️ PHASE 8: 키워드 체크 임시 스킵 (JSON 파싱 문제)")

            # 간단한 키워드 카운트 (수동)
            keyword_count = {}
            words_to_check = [keyword, "효과", "복용", "다이어트", "주사"]
            for word in words_to_check:
                count = full_content.count(word)
                keyword_count[word] = count

            check_result = {
                "keyword_count": keyword_count,
                "corrected_content": full_content
            }
            self.results["phase8_keyword_check"] = check_result

            print(f"✅ 키워드 체크 완료:")
            for word, count in keyword_count.items():
                status = "✅" if count <= 5 else "⚠️"
                print(f"   {status} {word}: {count}회")

            # 최종 원고
            final_content = full_content
            final_content = comprehensive_text_clean(format_paragraphs(final_content))

            # 최종 결과 정리
            final_result = {
                "title": final_title,
                "content": final_content,
                "word_count": len(final_content.replace(" ", "")),
                "character_count": len(final_content),
                "keyword": keyword,
                "category": category,
                "speaker_info": speaker_info,
                "subtitles": subtitles,
                "keywords": keywords,
                "keyword_count": check_result.get("keyword_count", {}),
                "generation_time": time.time() - self.start_time,
                "all_phases": self.results
            }

            self._print_final_summary(final_result)

            return final_result

        except Exception as e:
            print(f"❌ 원고 생성 중 오류 발생: {e}")
            raise

    def _next_phase(self, phase_name: str):
        """다음 단계로 진행"""
        self.current_phase += 1
        elapsed = time.time() - self.start_time if self.start_time else 0
        print(f"\n🔥 PHASE {self.current_phase}/{self.total_phases}: {phase_name}")
        print(f"⏱️ 경과시간: {elapsed:.1f}초")
        print("-" * 50)

    def _create_content_summary(self, contents: List[Dict[str, str]]) -> str:
        """본문 내용 요약 생성"""
        summary_parts = []
        for content_item in contents:
            subtitle = content_item["subtitle"]
            summary_parts.append(f"• {subtitle}")

        return "\n".join(summary_parts)

    def _assemble_full_content(
        self,
        title: str,
        intro: str,
        contents: List[Dict[str, str]],
        conclusion: str
    ) -> str:
        """전체 원고 조합"""
        parts = [title, "\n", intro, "\n"]

        for content_item in contents:
            subtitle = content_item["subtitle"]
            content = content_item["content"]
            parts.extend([f"\n## {subtitle}\n", content, "\n"])

        parts.extend([conclusion])

        return "".join(parts)

    def _print_final_summary(self, result: Dict[str, Any]):
        """최종 결과 요약 출력"""
        print("\n" + "=" * 60)
        print("🎉 스텝바이스텝 원고 생성 완료!")
        print("=" * 60)
        print(f"📝 제목: {result['title']}")
        print(f"📊 총 글자수: {result['word_count']:,}자")
        print(f"📊 총 문자수: {result['character_count']:,}자")
        print(f"⏱️ 생성시간: {result['generation_time']:.1f}초")
        print(f"🎭 화자: {result['category']} 카테고리")

        # 키워드 사용 현황
        print(f"\n🔍 키워드 사용 현황:")
        for word, count in result['keyword_count'].items():
            status = "✅" if count <= 5 else "⚠️"
            print(f"   {status} {word}: {count}회")

        # 소제목 목록
        print(f"\n📋 생성된 소제목:")
        for i, subtitle in enumerate(result['subtitles'], 1):
            print(f"   {i}. {subtitle}")

        print("=" * 60)


def step_by_step_generate(keyword: str, reference: str = "") -> str:
    """
    스텝바이스텝 원고 생성 함수 (간단 인터페이스)

    Args:
        keyword: 메인 키워드
        reference: 참조 원고 (선택적)

    Returns:
        완성된 원고 텍스트

    Raises:
        ValueError: 키워드 없음
        RuntimeError: 생성 실패
    """
    if not keyword or not keyword.strip():
        raise ValueError("키워드가 없습니다.")

    try:
        generator = StepByStepManuscriptGenerator()
        result = generator.generate_manuscript(keyword.strip(), reference)
        return result["content"]

    except Exception as e:
        print(f"❌ 스텝바이스텝 원고 생성 실패: {e}")
        raise RuntimeError(f"원고 생성 실패: {e}")


# 상세 결과를 원하는 경우 사용하는 함수
def step_by_step_generate_detailed(keyword: str, reference: str = "") -> Dict[str, Any]:
    """
    스텝바이스텝 원고 생성 함수 (상세 결과 포함)

    Args:
        keyword: 메인 키워드
        reference: 참조 원고 (선택적)

    Returns:
        완성된 원고와 모든 단계별 결과

    Raises:
        ValueError: 키워드 없음
        RuntimeError: 생성 실패
    """
    if not keyword or not keyword.strip():
        raise ValueError("키워드가 없습니다.")

    try:
        generator = StepByStepManuscriptGenerator()
        return generator.generate_manuscript(keyword.strip(), reference)

    except Exception as e:
        print(f"❌ 스텝바이스텝 원고 생성 실패: {e}")
        raise RuntimeError(f"원고 생성 실패: {e}")