#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MongoDB 데이터 수집기
모든 블로그 데이터를 하나의 파일에 모아서 Claude가 읽기 쉬운 형태로 저장
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

# 프로젝트 루트 추가
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

try:
    from mongodb_service import MongoDBService
    from utils.get_category_db_name import get_category_db_name

    MONGODB_AVAILABLE = True
except ImportError:
    MONGODB_AVAILABLE = False
    print("MongoDB 관련 모듈을 불러올 수 없습니다. 데모 데이터를 사용합니다.")


class BlogDataCollector:
    """블로그 데이터 수집 및 정리 클래스"""

    def __init__(self):
        self.db_service = None
        if MONGODB_AVAILABLE:
            try:
                self.db_service = MongoDBService()
            except Exception as e:
                print(f"MongoDB 연결 실패: {e}")
                self.db_service = None

    def get_available_databases(self) -> List[str]:
        """사용 가능한 데이터베이스 목록 반환"""
        if not self.db_service:
            return ["demo_wedding", "demo_diet", "demo_ophthalmology"]

        try:
            # MongoDB 클라이언트에서 데이터베이스 목록 가져오기
            db_names = self.db_service.client.list_database_names()
            # 시스템 데이터베이스 제외
            user_dbs = [db for db in db_names if db not in ["admin", "local", "config"]]
            return user_dbs
        except Exception as e:
            print(f"데이터베이스 목록 조회 실패: {e}")
            return []

    def collect_database_data(self, db_name: str) -> Dict[str, Any]:
        """특정 데이터베이스의 모든 데이터 수집"""
        if not self.db_service:
            return self._get_demo_data(db_name)

        try:
            # 데이터베이스 변경
            self.db_service.set_db_name(db_name)

            # 모든 분석 데이터 가져오기
            analysis_data = self.db_service.get_latest_analysis_data()

            # 추가 메타데이터
            collection_stats = {}
            collections = [
                "morphemes",
                "sentences",
                "expressions",
                "parameters",
                "subtitles",
                "templates",
            ]

            for collection in collections:
                try:
                    count = self.db_service.db[collection].count_documents({})
                    collection_stats[collection] = count
                except Exception as e:
                    collection_stats[collection] = f"오류: {e}"

            return {
                "database_name": db_name,
                "collection_stats": collection_stats,
                "analysis_data": analysis_data,
                "collected_at": datetime.now().isoformat(),
            }

        except Exception as e:
            print(f"데이터베이스 {db_name} 수집 실패: {e}")
            return {"database_name": db_name, "error": str(e)}

    def _get_demo_data(self, db_name: str) -> Dict[str, Any]:
        """데모 데이터 생성"""
        demo_data = {
            "database_name": db_name,
            "collection_stats": {
                "morphemes": 100,
                "sentences": 50,
                "expressions": 30,
                "parameters": 25,
                "subtitles": 15,
                "templates": 5,
            },
            "analysis_data": {
                "unique_words": ["제품", "사용", "효과", "만족", "추천"],
                "sentences": [
                    "정말 만족스러운 제품이었어요",
                    "사용해보니 효과가 확실하더라구요",
                    "가격대비 성능이 좋았습니다",
                ],
                "expressions": {
                    "긍정표현": ["만족스러웠어요", "효과적이었어요", "좋더라구요"],
                    "부정표현": ["아쉬웠던 점", "불편했던 부분", "개선 필요한"],
                    "경험표현": ["실제로 써보니", "개인적으로 느낀", "직접 경험한"],
                },
                "parameters": {
                    "가격": ["약 30만원", "50만원대", "100만원 이상"],
                    "시간": ["3개월", "6개월", "1년간"],
                    "효과": ["30% 개선", "확실한 변화", "눈에 띄는 효과"],
                },
                "subtitles": [
                    "제품 선택의 이유와 고민",
                    "가격과 성능 그리고 특징",
                    "실제 사용해본 솔직한 후기",
                    "장점과 단점 비교 분석",
                    "활용 팁과 종합 평가",
                ],
                "templates": [
                    {
                        "file_name": f"sample_{db_name}_1.txt",
                        "templated_text": "안녕하세요 오늘은 제품 후기를 공유해드리려고 해요...",
                    }
                ],
            },
            "collected_at": datetime.now().isoformat(),
        }
        return demo_data

    def collect_all_databases(self) -> Dict[str, Any]:
        """모든 데이터베이스 데이터 수집"""
        all_data = {
            "collection_info": {
                "collected_at": datetime.now().isoformat(),
                "collector_version": "1.0",
                "mongodb_available": MONGODB_AVAILABLE,
            },
            "databases": {},
        }

        db_names = self.get_available_databases()
        print(f"수집할 데이터베이스: {db_names}")

        for db_name in db_names:
            print(f"데이터베이스 수집 중: {db_name}")
            db_data = self.collect_database_data(db_name)
            all_data["databases"][db_name] = db_data

        return all_data

    def format_for_claude(self, all_data: Dict[str, Any]) -> str:
        """Claude가 읽기 쉬운 텍스트 형태로 포맷팅"""

        output_lines = []

        # 헤더
        output_lines.append("=" * 80)
        output_lines.append("블로그 데이터 컬렉션")
        output_lines.append("=" * 80)
        output_lines.append("")

        # 수집 정보
        collection_info = all_data.get("collection_info", {})
        output_lines.append(
            f"수집 시간: {collection_info.get('collected_at', 'Unknown')}"
        )
        output_lines.append(
            f"MongoDB 연결: {'성공' if collection_info.get('mongodb_available') else '실패 (데모 데이터)'}"
        )
        output_lines.append(f"총 데이터베이스 수: {len(all_data.get('databases', {}))}")
        output_lines.append("")

        # 각 데이터베이스별 데이터
        for db_name, db_data in all_data.get("databases", {}).items():
            output_lines.append("-" * 50)
            output_lines.append(f"데이터베이스: {db_name}")
            output_lines.append("-" * 50)
            output_lines.append("")

            # 컬렉션 통계
            if "collection_stats" in db_data:
                output_lines.append("📊 컬렉션 통계:")
                for collection, count in db_data["collection_stats"].items():
                    output_lines.append(f"  - {collection}: {count}개")
                output_lines.append("")

            # 분석 데이터
            analysis_data = db_data.get("analysis_data", {})

            # 고유 단어
            unique_words = analysis_data.get("unique_words", [])
            if unique_words:
                output_lines.append("📝 고유 단어 (상위 20개):")
                for word in unique_words[:20]:
                    output_lines.append(f"  - {word}")
                output_lines.append("")

            # 문장 예시
            sentences = analysis_data.get("sentences", [])
            if sentences:
                output_lines.append("💬 문장 예시 (상위 10개):")
                for i, sentence in enumerate(sentences[:10], 1):
                    output_lines.append(f"  {i}. {sentence}")
                output_lines.append("")

            # 표현 라이브러리
            expressions = analysis_data.get("expressions", {})
            if expressions:
                output_lines.append("🎭 표현 라이브러리:")
                for category, expr_list in expressions.items():
                    output_lines.append(f"  [{category}]")
                    for expr in expr_list[:5]:  # 상위 5개만
                        output_lines.append(f"    - {expr}")
                output_lines.append("")

            # 파라미터
            parameters = analysis_data.get("parameters", {})
            if parameters:
                output_lines.append("⚙️ 파라미터:")
                for category, param_list in parameters.items():
                    output_lines.append(f"  [{category}]")
                    for param in param_list[:5]:  # 상위 5개만
                        output_lines.append(f"    - {param}")
                output_lines.append("")

            # 부제목
            subtitles = analysis_data.get("subtitles", [])
            if subtitles:
                output_lines.append("📋 부제목 예시:")
                for subtitle in subtitles[:10]:
                    output_lines.append(f"  - {subtitle}")
                output_lines.append("")

            # 템플릿
            templates = analysis_data.get("templates", [])
            if templates:
                output_lines.append("📄 템플릿 예시:")
                for i, template in enumerate(templates[:3], 1):
                    file_name = template.get("file_name", "Unknown")
                    content = template.get("templated_text", "")
                    output_lines.append(f"  {i}. {file_name}")
                    output_lines.append(f"     {content[:100]}...")  # 첫 100자만
                output_lines.append("")

            output_lines.append("")

        return "\n".join(output_lines)

    def save_data(self, data: Dict[str, Any], format_type: str = "both") -> List[str]:
        """데이터 저장 (JSON, 텍스트, 또는 둘 다)"""
        saved_files = []
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # claude 폴더 내에 data 서브폴더 생성
        data_dir = Path(__file__).parent / "data"
        data_dir.mkdir(exist_ok=True)

        if format_type in ["json", "both"]:
            # JSON 형태로 저장
            json_file = data_dir / f"blog_data_{timestamp}.json"
            with open(json_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            saved_files.append(str(json_file))
            print(f"JSON 파일 저장: {json_file}")

        if format_type in ["text", "both"]:
            # 텍스트 형태로 저장
            text_file = data_dir / f"blog_data_{timestamp}.txt"
            formatted_text = self.format_for_claude(data)
            with open(text_file, "w", encoding="utf-8") as f:
                f.write(formatted_text)
            saved_files.append(str(text_file))
            print(f"텍스트 파일 저장: {text_file}")

        return saved_files


def main():
    """메인 함수"""
    print("=" * 60)
    print("MongoDB 블로그 데이터 수집기")
    print("=" * 60)

    collector = BlogDataCollector()

    # 사용 가능한 데이터베이스 확인
    databases = collector.get_available_databases()
    print(f"발견된 데이터베이스: {databases}")

    if not databases:
        print("수집할 데이터베이스가 없습니다.")
        return

    # 모든 데이터베이스 데이터 수집
    print("\n데이터 수집 시작...")
    all_data = collector.collect_all_databases()

    # 파일로 저장
    print("\n파일 저장 중...")
    saved_files = collector.save_data(all_data, format_type="both")

    print(f"\n✅ 데이터 수집 완료!")
    print(f"저장된 파일: {saved_files}")

    # 간단한 통계 출력
    total_dbs = len(all_data.get("databases", {}))
    print(f"📊 총 {total_dbs}개 데이터베이스 수집 완료")


if __name__ == "__main__":
    main()
