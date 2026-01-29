from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException
from fastapi.concurrency import run_in_threadpool

from mongodb_service import MongoDBService
from schema.search import SearchRequest
from config import MONGO_URI
from pymongo import MongoClient
from _constants.categories import CATEGORIES
from utils.logger import log

router = APIRouter()

# 모든 카테고리 목록 (categories.py에서 import)
COLLECTION_LIST = CATEGORIES


def search_all(keyword: str, limit: int = 20) -> List[Dict[str, Any]]:
    """
    모든 카테고리 DB에서 키워드 검색

    Args:
        keyword: 검색할 키워드
        limit: 반환할 결과 수

    Returns:
        검색 결과 리스트 (score 내림차순 정렬)
    """
    client = MongoClient(MONGO_URI)
    results = []

    try:
        for category in COLLECTION_LIST:
            try:
                db = client[category]
                collection = db["manuscripts"]

                # 정규식 검색 (text index 없이도 동작)
                query = {
                    "$or": [
                        {"content": {"$regex": keyword, "$options": "i"}},
                        {"keyword": {"$regex": keyword, "$options": "i"}},
                    ],
                    "deleted": {"$ne": True}
                }

                # 검색 실행 (최신순 정렬)
                cursor = collection.find(query).sort("createdAt", -1).limit(limit)

                for doc in cursor:
                    # _id를 문자열로 변환
                    if "_id" in doc:
                        doc["_id"] = str(doc["_id"])

                    # 어느 카테고리에서 나왔는지 표시
                    doc["__category"] = category

                    # 간단한 점수 계산 (keyword 일치도)
                    score = 0
                    if "keyword" in doc and keyword.lower() in doc["keyword"].lower():
                        score += 10
                    if "content" in doc and keyword.lower() in doc["content"].lower():
                        score += doc["content"].lower().count(keyword.lower())
                    doc["__score"] = score

                    results.append(doc)

            except Exception as e:
                # 해당 카테고리 DB가 없거나 오류가 나도 계속 진행
                log.warning(f"카테고리 검색 오류", category=category)
                continue

        # 점수로 정렬하고 상위 결과만 반환
        results.sort(key=lambda d: d.get("__score", 0), reverse=True)
        return results[:limit]

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"통합 검색 중 오류 발생: {str(e)}"
        )
    finally:
        client.close()


MAX_QUERY_LENGTH = 100


@router.post("/search/all")
async def search_all_endpoint(body: SearchRequest):
    """
    모든 카테고리에서 키워드 통합 검색

    - **q**: 검색 키워드 (필수)
    - **limit**: 결과 수 제한 (기본값: 20, 최대: 100)

    Returns:
        {
            "query": 검색어,
            "count": 결과 수,
            "results": [
                {
                    ...원고 데이터...,
                    "__category": "카테고리명",
                    "__score": 검색 점수
                }
            ]
        }
    """
    query = body.q.strip()

    if not query:
        raise HTTPException(status_code=400, detail="검색 키워드를 입력해주세요.")

    if len(query) > MAX_QUERY_LENGTH:
        raise HTTPException(
            status_code=400,
            detail=f"검색어가 너무 깁니다. (최대 {MAX_QUERY_LENGTH}자)"
        )

    docs = await run_in_threadpool(search_all, query, body.limit)
    log.success("통합 검색", query=query[:20], count=len(docs))

    return {
        "query": query,
        "count": len(docs),
        "results": docs,
    }
