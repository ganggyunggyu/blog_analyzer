import re
import random
from typing import Dict, Any, List
from pymongo.collection import Collection
from pymongo import DESCENDING


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
        """템플릿 컬렉션에 텍스트 인덱스 생성"""
        try:
            # 텍스트 인덱스 생성 (언어 설정 없이)
            from pymongo import TEXT

            index_spec = [
                ("file_name", TEXT),
                ("templated_text", TEXT)
            ]
            coll.create_index(index_spec, name="text_search_index")
            print("✅ 텍스트 인덱스 생성 완료! (기본 언어 설정)")
            return True
        except Exception as e:
            print(f"❌ 텍스트 인덱스 생성 실패: {e}")
            return False

    def _get_simple_regex_search(coll: Collection, keyword: str, top_n: int) -> List[Dict[str, Any]]:
        """간단한 정규표현식 검색"""
        search_results = list(coll.find({
            "$or": [
                {"file_name": {"$regex": keyword, "$options": "i"}},
                {"templated_text": {"$regex": keyword, "$options": "i"}}
            ]
        }).limit(top_n))
        return search_results

    selected_template = None
    selection_method = ""
    if not templates:
        print("❌ 로컬 templates 리스트가 비어있습니다!")
        return {"selected_template": None, "selection_method": "no-templates"}

    print(f"📊 사용 가능한 템플릿 개수: {len(templates)}")

    if keyword.strip():
        # 띄어쓰기를 언더스코어로 변환하여 파일명 매칭률 향상
        search_keyword = keyword.replace(" ", "_")
        print(f"🔤 원본 키워드: '{keyword}' → 검색용: '{search_keyword}'")
        try:
            # 1) 텍스트 인덱스 확인 및 생성
            has_index = _has_text_index(collection)

            print(f"🔍 텍스트 인덱스 상태 확인: {'✅ 존재함' if has_index else '❌ 없음'}")

            if not has_index:
                print("🔧 텍스트 인덱스가 없습니다. 생성을 시도합니다...")
                if _create_text_index(collection):
                    has_index = True
                    print("🎉 텍스트 인덱스 생성 후 상태: ✅ 생성 완료")
                else:
                    print("⚠️  텍스트 인덱스 생성 실패, regex 검색으로 계속 진행합니다.")

            if has_index:
                print("⚡ MongoDB 텍스트 인덱스 검색 사용")
                # 텍스트 인덱스 사용
                cursor = (
                    collection.find(
                        {"$text": {"$search": search_keyword}},
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
                    selection_method = f"text-index(top{len(top_docs)})-rand"
                else:
                    # 텍스트 인덱스 검색 실패시 regex로 fallback
                    print("⚠️  텍스트 인덱스 검색 결과 없음, regex 검색으로 전환")
                    print(f"🔍 검색 키워드: {search_keyword}")
                    top_docs = _get_simple_regex_search(collection, search_keyword, top_n)
                    print(f"📝 regex 검색 결과 개수: {len(top_docs) if top_docs else 0}")
            else:
                # 2) 텍스트 인덱스 생성 실패 → regex 기반 점수화
                print("📝 텍스트 인덱스 없음 - regex 기반 검색 사용")
                top_docs = _get_simple_regex_search(collection, search_keyword, top_n)

            if top_docs:
                picked = random.choice(top_docs)
                selected_template = {
                    "_id": str(picked.get("_id")),
                    "file_name": picked.get("file_name"),
                    "templated_text": picked.get("templated_text"),
                }
                selection_method = f"regex-search(top{len(top_docs)})-rand"
            else:
                # 검색 결과 없으면 로컬에서 랜덤
                picked = random.choice(templates)
                selected_template = {
                    "_id": str(picked.get("_id", "")),
                    "file_name": picked.get("file_name"),
                    "templated_text": picked.get("templated_text"),
                }
                selection_method = "no-search-results-local-rand"

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
