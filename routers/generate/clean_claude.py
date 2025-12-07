"""Clean Claude 라우터 (프롬프트 없음)"""
from datetime import datetime

from fastapi import APIRouter, HTTPException
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel

from llm.clean_claude_service import clean_claude_gen, MODEL_NAME
from mongodb_service import MongoDBService
from utils.get_category_db_name import get_category_db_name
from utils.progress_logger import progress

router = APIRouter()


class GenerateRequest(BaseModel):
    service: str = "clean-claude"
    keyword: str
    ref: str = ""


@router.post("/generate/clean-claude")
async def generate_clean_claude(request: GenerateRequest):
    """프롬프트 없이 Claude로 생성"""
    service = (request.service or "clean-claude").lower()
    keyword = (request.keyword or "").strip()
    ref = request.ref or ""

    if not keyword:
        raise HTTPException(status_code=400, detail="keyword는 필수입니다.")

    category = await get_category_db_name(keyword=keyword)

    db_service = MongoDBService()
    db_service.set_db_name(db_name=category)

    is_ref = bool(ref and ref.strip())
    print(
        f"[GEN] service={service} | model={MODEL_NAME} | category={category} | keyword={keyword} | hasRef={is_ref}"
    )

    try:
        with progress(label=f"{service}:{MODEL_NAME}:{keyword}"):
            generated_manuscript = await run_in_threadpool(
                clean_claude_gen,
                user_instructions=keyword,
                ref=ref,
                category=category,
            )

        if generated_manuscript:
            document = {
                "content": generated_manuscript,
                "createdAt": datetime.now(),
                "engine": MODEL_NAME,
                "service": service,
                "category": category,
                "keyword": keyword,
            }
            try:
                db_service.insert_document("manuscripts", document)
                document["_id"] = str(document["_id"])
                return document
            except Exception:
                raise HTTPException(
                    status_code=500, detail="생성 성공했지만 DB 저장에 실패했습니다."
                )
        else:
            raise HTTPException(
                status_code=500,
                detail="원고 생성에 실패했습니다. Clean Claude 모델 응답을 확인해주세요.",
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"원고 생성 중 오류 발생: {e}")
    finally:
        try:
            db_service.close_connection()
        except Exception:
            pass
