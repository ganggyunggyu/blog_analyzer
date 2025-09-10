from fastapi import APIRouter, HTTPException
from starlette.concurrency import run_in_threadpool
from pydantic import BaseModel


from mongodb_service import MongoDBService
from _constants.Model import Model
from utils.get_category_db_name import get_category_db_name
from llm.gemini_service import get_gemini_response


class GenerateRequest(BaseModel):
    service: str = "gemini"
    keyword: str
    ref: str = ""


router = APIRouter()
GEMINI_MODEL_NAME = Model.GEMINI_2_5_PRO


@router.post("/generate/gemini")
async def generate_manuscript_gemini_api(request: GenerateRequest):
    """
    Gemini로 원고 생성 (GPT/Claude 엔드포인트와 동일한 처리 흐름).
    동기 SDK 호출은 threadpool로 오프로딩해서 동시 요청에 안전.
    """
    service = (request.service or "gemini").lower()
    keyword = (request.keyword or "").strip()
    ref = request.ref or ""

    if not keyword:
        raise HTTPException(status_code=400, detail="keyword는 필수입니다.")

    # 1) 카테고리 판별
    category = get_category_db_name(keyword=keyword)

    db_service = MongoDBService()
    db_service.set_db_name(db_name=category)

    # 디버그 출력: 어떤 서비스/모델/키워드/참조 여부로 실행하는지 표시
    is_ref = bool(ref and ref.strip())
    print(
        f"[GEN] service={service} | model={GEMINI_MODEL_NAME} | category={category} | keyword={keyword} | hasRef={is_ref}"
    )

    try:
        # 2) 최신 분석 데이터 로드
        analysis_data = db_service.get_latest_analysis_data()
        unique_words = analysis_data.get("unique_words", [])
        sentences = analysis_data.get("sentences", [])
        expressions = analysis_data.get("expressions", {})
        parameters = analysis_data.get("parameters", {})

        if not (unique_words and sentences and expressions and parameters):
            raise HTTPException(
                status_code=500,
                detail="MongoDB에 원고 생성을 위한 충분한 분석 데이터가 없습니다. 먼저 분석을 실행하고 저장해주세요.",
            )

        generated = await run_in_threadpool(
            get_gemini_response,
            keyword,
            ref,
        )

        if not generated or str(generated).startswith("An error occurred:"):
            raise HTTPException(
                status_code=500,
                detail=f"Gemini API 응답 오류: {generated or 'empty response'}",
            )

        # 4) DB 저장
        import time

        doc = {
            "content": generated,
            "timestamp": time.time(),
            "engine": "gemini",
            "keyword": keyword,
            "category": category,
        }
        try:
            db_service.insert_document("manuscripts", doc)
            doc["_id"] = str(doc["_id"])
            return doc
        except Exception:
            # 저장 실패해도 생성물은 반환할지, 에러낼지 정책에 따라 결정
            return doc  # 또는 raise HTTPException(500, "생성 성공했지만 DB 저장 실패")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"원고 생성 중 오류: {e}")
    finally:
        try:
            db_service.close_connection()
        except Exception:
            pass
