import random
from typing import Dict, Any, List
from pymongo.collection import Collection


def select_template(
    collection: Collection,
    templates: List[Dict[str, Any]],
    keyword: str = "",
    top_n: int = 3,
) -> Dict[str, Any]:
    """
    MongoDB 컬렉션 + 로컬 리스트에서 템플릿 선택

    1. 키워드가 있으면:
        - 텍스트 인덱스 있으면 → textScore 기준 상위 top_n → 랜덤
        - 없으면 regex 매칭 + 간이 점수화 → 상위 top_n → 랜덤
    2. 키워드 없거나 결과 없으면:
        - 로컬 templates 리스트에서 랜덤
    """

    def _has_text_index(coll: Collection) -> bool:
        try:
            for idx in coll.list_indexes():
                if idx.get("weights") or idx.get("textIndexVersion"):
                    return True
        except Exception:
            pass
        return False

    def _create_text_index(coll: Collection) -> bool:
        """템플릿 컬렉션에 텍스트 인덱스 생성 (제목만)"""
        try:
            # 제목(file_name)만으로 텍스트 인덱스 생성
            from pymongo import TEXT

            index_spec = [("file_name", TEXT)]
            coll.create_index(index_spec, name="filename_text_index")
            print("✅ 제목 텍스트 인덱스 생성 완료!")
            return True
        except Exception as e:
            print(f"❌ 텍스트 인덱스 생성 실패: {e}")
            return False

    def _normalize_text(text: str) -> str:
        """텍스트 정규화: 띄어쓰기, 특수문자 제거"""
        import re

        # 한글, 영문, 숫자만 남기고 모두 제거
        return re.sub(r"[^\w가-힣]", "", text).lower()

    def _get_filename_smart_search(
        coll: Collection, keyword: str, top_n: int
    ) -> List[Dict[str, Any]]:
        """완전 정규화된 제목 비교 검색"""
        # 키워드 정규화
        normalized_keyword = _normalize_text(keyword)

        pipeline = [
            # 1단계: file_name 완전 정규화 (띄어쓰기, 특수문자 제거)
            {
                "$addFields": {
                    "normalized_filename": {
                        "$toLower": {
                            "$replaceAll": {
                                "input": {
                                    "$replaceAll": {
                                        "input": "$file_name",
                                        "find": "_",
                                        "replacement": "",
                                    }
                                },
                                "find": " ",
                                "replacement": "",
                            }
                        }
                    }
                }
            },
            # 2단계: 정규화된 파일명에서 정규화된 키워드 포함 여부 확인
            {
                "$match": {
                    "normalized_filename": {
                        "$regex": normalized_keyword,
                        "$options": "i",
                    }
                }
            },
            # 3단계: 원본 필드만 반환
            {"$project": {"file_name": 1, "templated_text": 1, "_id": 1}},
            {"$limit": top_n},
        ]
        return list(coll.aggregate(pipeline))

    def _get_simple_regex_search(
        coll: Collection, keyword: str, top_n: int
    ) -> List[Dict[str, Any]]:
        """간단한 정규표현식 검색 (제목+본문)"""
        search_results = list(
            coll.find(
                {
                    "$or": [
                        {"file_name": {"$regex": keyword, "$options": "i"}},
                        {"templated_text": {"$regex": keyword, "$options": "i"}},
                    ]
                }
            ).limit(top_n)
        )
        return search_results

    selected_template = None
    selection_method = ""
    if not templates:
        print("❌ 로컬 templates 리스트가 비어있습니다!")
        return {"selected_template": None, "selection_method": "no-templates"}

    print(f"📊 사용 가능한 템플릿 개수: {len(templates)}")

    if keyword.strip():
        # 원본 키워드 그대로 사용 (DB에서 _를 공백으로 치환해서 비교)
        search_keyword = keyword.strip()
        print(f"🔤 검색 키워드: '{search_keyword}'")
        try:
            # 1) 텍스트 인덱스 확인 및 생성
            has_index = _has_text_index(collection)

            print(
                f"🔍 텍스트 인덱스 상태 확인: {'✅ 존재함' if has_index else '❌ 없음'}"
            )

            if not has_index:
                print("🔧 텍스트 인덱스가 없습니다. 생성을 시도합니다...")
                if _create_text_index(collection):
                    has_index = True
                    print("🎉 텍스트 인덱스 생성 후 상태: ✅ 생성 완료")
                else:
                    print("⚠️  텍스트 인덱스 생성 실패, regex 검색으로 계속 진행합니다.")

            if has_index:
                print("⚡ MongoDB 텍스트 인덱스 검색 사용 (제목 기반)")
                # 키워드 정규화 후 텍스트 인덱스 검색
                normalized_keyword = _normalize_text(search_keyword)
                print(f"🔍 정규화된 키워드: '{normalized_keyword}'")
                cursor = (
                    collection.find(
                        {"$text": {"$search": normalized_keyword}},
                        projection={
                            "file_name": 1,
                            "templated_text": 1,
                            "score": {"$meta": "textScore"},
                        },
                    )
                    .sort([("score", {"$meta": "textScore"})])
                    .limit(top_n)
                )

                top_docs = list(cursor)
                if top_docs:
                    picked = random.choice(top_docs)
                    selected_template = {
                        "_id": str(picked.get("_id")),
                        "file_name": picked.get("file_name"),
                        "templated_text": picked.get("templated_text"),
                    }
                    selection_method = f"text-index-filename(top{len(top_docs)})-rand"
                else:
                    # 텍스트 인덱스 검색 실패시 스마트 제목 검색으로 fallback
                    print(
                        "⚠️  제목 텍스트 인덱스 검색 결과 없음, 스마트 제목 검색으로 전환"
                    )
                    print(f"🔍 검색 키워드: {search_keyword}")
                    top_docs = _get_filename_smart_search(
                        collection, search_keyword, top_n
                    )
                    print(
                        f"📝 스마트 제목 검색 결과 개수: {len(top_docs) if top_docs else 0}"
                    )

                    # 스마트 검색도 실패시 전체 검색
                    if not top_docs:
                        print("🔄 스마트 검색 실패, 전체 검색으로 재시도")
                        top_docs = _get_simple_regex_search(
                            collection, search_keyword, top_n
                        )
                        print(
                            f"📝 전체 검색 결과 개수 (제목+본문): {len(top_docs) if top_docs else 0}"
                        )
            else:
                # 2) 텍스트 인덱스 생성 실패 → 스마트 검색 먼저 시도
                print("📝 텍스트 인덱스 없음 - 스마트 제목 검색 사용")
                top_docs = _get_filename_smart_search(collection, search_keyword, top_n)
                print(
                    f"📝 스마트 제목 검색 결과 개수: {len(top_docs) if top_docs else 0}"
                )

                # 스마트 검색 실패시 전체 검색
                if not top_docs:
                    print("🔄 스마트 검색 실패, 전체 검색으로 재시도")
                    top_docs = _get_simple_regex_search(
                        collection, search_keyword, top_n
                    )
                    print(
                        f"📝 전체 검색 결과 개수 (제목+본문): {len(top_docs) if top_docs else 0}"
                    )

            if top_docs:
                picked = random.choice(top_docs)
                selected_template = {
                    "_id": str(picked.get("_id")),
                    "file_name": picked.get("file_name"),
                    "templated_text": picked.get("templated_text"),
                }
                # selection_method 결정 로직
                if len(top_docs) > 0:
                    # 어떤 검색 방법으로 찾았는지 확인 필요
                    selection_method = f"smart-or-full-search(top{len(top_docs)})-rand"
                else:
                    selection_method = "no-results"
            else:
                # 검색 결과 없으면 로컬에서 랜덤 (3단계)
                print("🎲 모든 검색 실패, 랜덤 선택으로 진행")
                picked = random.choice(templates)
                selected_template = {
                    "_id": str(picked.get("_id", "")),
                    "file_name": picked.get("file_name"),
                    "templated_text": picked.get("templated_text"),
                }
                selection_method = "fallback-random-selection"

        except Exception as e:
            # 검색 오류시 로컬에서 랜덤
            picked = random.choice(templates)
            selected_template = {
                "_id": str(picked.get("_id", "")),
                "file_name": picked.get("file_name"),
                "templated_text": picked.get("templated_text"),
            }
            selection_method = f"search-error-local-rand:{str(e)[:30]}"
    else:
        picked = random.choice(templates)
        selected_template = {
            "_id": str(picked.get("_id", "")),
            "file_name": picked.get("file_name"),
            "templated_text": picked.get("templated_text"),
        }
        selection_method = "no-keyword-local-rand"

    return {
        "selected_template": selected_template,
        "selection_method": selection_method,
    }
