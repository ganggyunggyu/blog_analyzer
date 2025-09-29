from fastapi import HTTPException, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from claude.claude_service import claude_blog_generator
from llm.claude_service import claude_gen, ClaudeModel

from mongodb_service import MongoDBService

from llm.gemini_service import get_gemini_response
from utils.get_category_db_name import get_category_db_name
from typing import Optional
from fastapi.concurrency import run_in_threadpool
import asyncio
from fastapi import FastAPI, HTTPException
from fastapi.concurrency import run_in_threadpool
import os
from utils.progress_logger import progress

router = APIRouter()


class GenerateRequest(BaseModel):
    service: str = "claude"
    keyword: str
    ref: str = ""


@router.post("/generate/claude")
async def generate_manuscript_claude_api(request: GenerateRequest):
    """
    Claude로 원고 생성 (GPT 엔드포인트와 동일한 처리 흐름)
    """
    service = (request.service or "claude").lower()
    keyword = (request.keyword or "").strip()
    ref = request.ref or ""

    if not keyword:
        raise HTTPException(status_code=400, detail="keyword는 필수입니다.")

    # 1) 카테고리 판별
    category = await get_category_db_name(keyword=keyword)

    db_service = MongoDBService()
    db_service.set_db_name(db_name=category)

    # 디버그 출력: 어떤 서비스/모델/키워드/참조 여부로 실행하는지 표시
    model_name = ClaudeModel.SONNET_3_7.value
    is_ref = bool(ref and ref.strip())
    print(
        f"[GEN] service={service} | model={model_name} | category={category} | keyword={keyword} | hasRef={is_ref}"
    )

    try:
        with progress(label=f"{service}:{model_name}:{keyword}"):
            generated_manuscript = await run_in_threadpool(
                claude_gen,
                keyword=keyword,
                ref=ref,
            )

        if generated_manuscript:
            import time

            current_time = time.time()
            document = {
                "content": generated_manuscript,
                "timestamp": current_time,
            }
            try:
                db_service.insert_document("manuscripts", document)
                # pymongo insert 후 document에 _id가 주입됨
                document["_id"] = str(document["_id"])
                return document
            except Exception:
                # 저장 실패 시에도 생성물은 돌려주고 싶다면:
                # return {"content": generated_manuscript, "timestamp": current_time}
                raise HTTPException(
                    status_code=500, detail="생성 성공했지만 DB 저장에 실패했습니다."
                )
        else:
            raise HTTPException(
                status_code=500,
                detail="원고 생성에 실패했습니다. Claude 모델 응답을 확인해주세요.",
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
