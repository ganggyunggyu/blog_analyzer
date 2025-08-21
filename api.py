# 표준 라이브러리
import os
import asyncio

# 외부 라이브러리
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 라우터
from routers import ingest
from routers.test import test
from routers.generate import gemini, gpt, gpt_5, gpt_4_v2, gpt_5_v2
from routers.category import keyword
from routers.analysis import get_sub_title

LLM_CONCURRENCY = int(os.getenv("LLM_CONCURRENCY", "3"))
llm_semaphore = asyncio.Semaphore(LLM_CONCURRENCY)

app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ingest.router)
app.include_router(test.router)
app.include_router(gemini.router)
app.include_router(gpt.router)
app.include_router(gpt_5.router)
app.include_router(keyword.router)
app.include_router(get_sub_title.router)
app.include_router(gpt_4_v2.router)
app.include_router(gpt_5_v2.router)
