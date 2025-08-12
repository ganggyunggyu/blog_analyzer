# routes/generate_gemini.py (예시)
from fastapi import APIRouter, HTTPException
from starlette.concurrency import run_in_threadpool
from pydantic import BaseModel
import time

from mongodb_service import MongoDBService
from utils.categorize_keyword_with_ai import categorize_keyword_with_ai
from llm.gemini_service import get_gemini_response  # 앞서 만든 함수
# GenerateRequest는 기존과 동일한 스키마를 사용한다고 가정
# service, keyword, ref 필드
class GenerateRequest(BaseModel):
    service: str = "gemini"
    keyword: str
    ref: str = ""

router = APIRouter()

@router.post("/generate/gemini")
async def generate_manuscript_gemini(request: GenerateRequest):
    """
    Gemini 기반 원고 생성 (동시 처리 OK: blocking 호출은 threadpool로 오프로딩).
    """
    keyword = (request.keyword or "").strip()
    ref = request.ref or ""

    if not keyword:
        raise HTTPException(status_code=400, detail="'keyword' 필드는 필수입니다.")

    # 1) 카테고리 결정
    category = categorize_keyword_with_ai(keyword=keyword)

    db_service = MongoDBService()
    db_service.set_db_name(db_name=category)

    print(f"""
서비스: gemini
키워드: {request.keyword}
참조문서 유무: {len(ref) != 0}
선택된 카테고리: {category}
""")

    try:
        # 2) 분석 데이터 로드
        analysis_data = db_service.get_latest_analysis_data()
        unique_words = analysis_data.get("unique_words", [])
        sentences = analysis_data.get("sentences", [])
        expressions = analysis_data.get("expressions", {})
        parameters  = analysis_data.get("parameters", {})

        if not (unique_words and sentences and expressions and parameters):
            raise HTTPException(
                status_code=500,
                detail="MongoDB에 원고 생성을 위한 충분한 분석 데이터가 없습니다. 먼저 분석을 실행하고 저장해주세요."
            )

        # 3) Gemini 호출 (threadpool로)
        content = await run_in_threadpool(
            get_gemini_response,
            unique_words,
            sentences,
            expressions,
            parameters,
            keyword,     # user_instructions
            ref,         # ref
            # 옵션: 필요한 경우 모델/토큰 조정 가능
            # model="gemini-1.5-pro",
            # max_output_tokens=3000,
            # temperature=0.2,
            # top_p=0.95,
        )

        if not content or str(content).startswith("An error occurred:"):
            raise HTTPException(
                status_code=500,
                detail=f"Gemini API 응답 오류: {content if content else 'empty response'}"
            )

        # 4) DB 저장
        now = time.time()
        doc = {
            "content": content,
            "timestamp": now,
            "engine": "gemini",
            "keyword": keyword,
            "category": category,
        }

        try:
            db_service.insert_document("manuscripts", doc)
            doc["_id"] = str(doc["_id"])
            return doc
        except Exception as e:
            print(f"데이터베이스 저장 실패: {e}")
            # 저장 실패해도 생성 결과는 반환
            return {"content": content, "timestamp": now, "engine": "gemini", "category": category}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"서버 내부 오류: {e}")
    finally:
        db_service.close_connection()