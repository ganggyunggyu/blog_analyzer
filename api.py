# 표준 라이브러리
import os
import asyncio
from typing import Optional

# 외부 라이브러리
from fastapi import FastAPI, HTTPException, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel
import logging

logger = logging.getLogger("uvicorn.error")  # uvicorn 메인 로그 스트림에 합류
logger.setLevel(logging.INFO)

# 내부 서비스 / 유틸
from main import run_manuscript_generation
from mongodb_service import MongoDBService
from llm.claude_service import get_claude_response
from llm.gemini_service import get_gemini_response
from utils.categorize_keyword_with_ai import categorize_keyword_with_ai

# 라우터
from routers import ingest
from routers.test import test
from routers.generate import gemini
from routers.generate import gpt
from routers.category import keyword
from routers.analysis import get_sub_title

LLM_CONCURRENCY = int(os.getenv("LLM_CONCURRENCY", "3"))
llm_semaphore = asyncio.Semaphore(LLM_CONCURRENCY)

app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ingest.router)
app.include_router(test.router)
app.include_router(gemini.router)
app.include_router(gpt.router)
app.include_router(keyword.router)
app.include_router(get_sub_title.router)


class GenerateRequest(BaseModel):
    service: str
    keyword: str
    ref: Optional[str] = None
    
    

