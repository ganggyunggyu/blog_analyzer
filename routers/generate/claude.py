from fastapi import HTTPException, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from main import run_manuscript_generation
from mongodb_service import MongoDBService
from llm.claude_service import get_claude_response
from llm.gemini_service import get_gemini_response
from utils.categorize_keyword_with_ai import categorize_keyword_with_ai
from typing import Optional
from fastapi.concurrency import run_in_threadpool
import asyncio
from fastapi import FastAPI, HTTPException
from fastapi.concurrency import run_in_threadpool
import os

router = APIRouter()

class GenerateRequest(BaseModel):
    service: str = "gemini"
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
    category = categorize_keyword_with_ai(keyword=keyword)

    db_service = MongoDBService()
    db_service.set_db_name(db_name=category)

    print(f'''
서비스: {service}
키워드: {request.keyword}
참조문서 유무: {len(ref) != 0}
선택된 카테고리: {category}
''')

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
                detail="MongoDB에 원고 생성을 위한 충분한 분석 데이터가 없습니다. 먼저 분석을 실행하고 저장해주세요."
            )

        # 3) Claude 호출 (스레드풀로 블로킹 IO 분리)
        generated_manuscript = await run_in_threadpool(
            get_claude_response,
            unique_words=unique_words,
            sentences=sentences,
            expressions=expressions,
            parameters=parameters,
            user_instructions=keyword,
            ref=ref
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
            except Exception as e:
                print(f"데이터베이스에 저장 실패: {e}")
                # 저장 실패 시에도 생성물은 돌려주고 싶다면:
                # return {"content": generated_manuscript, "timestamp": current_time}
                raise HTTPException(status_code=500, detail="생성 성공했지만 DB 저장에 실패했습니다.")
        else:
            raise HTTPException(status_code=500, detail="원고 생성에 실패했습니다. Claude 모델 응답을 확인해주세요.")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"원고 생성 중 오류 발생: {e}")
    finally:
        try:
            db_service.close_connection()
        except Exception:
            pass