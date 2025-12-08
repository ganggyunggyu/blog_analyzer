# 표준 라이브러리
import os
import asyncio

# 외부 라이브러리
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 라우터
from routers import ingest

from routers.test import test
from routers.generate import (
    chunk,
    claude,
    clean_claude,
    clean_deepseek,
    deepseek,
    gemini,
    gemini_3_pro,
    gpt,
    gpt_5,
    gpt_4_v2,
    gpt_4_v3,
    gpt_5_v2,
    kkk,
    grok,
    mdx_post,
    restaurant,
    restaurant_claude,
    restaurant_grok,
    restaurant_gpt5,
    solar,
    gpt_merge,
    my,
    song,
    gang,
    step_by_step,
    clean,
    synonym,
    review,
    news,
    deep_search,
    translation_compare,
    xai_prompt_engineer,
    openai_prompt_engineer,
    story_analysis,
    requirement_analysis,
)
from routers.category import keyword
from routers.analysis import get_sub_title, upload_text, analyzer_router
from routers.ref import get_ref
from routers.search import (
    keyword as search_keyword,
    manuscript as search_manuscript,
    all as search_all,
)

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
app.include_router(gemini_3_pro.router)
app.include_router(claude.router)
app.include_router(clean_claude.router)
app.include_router(gpt.router)
app.include_router(gpt_5.router)
app.include_router(keyword.router)
app.include_router(get_sub_title.router)
app.include_router(gpt_4_v2.router)
app.include_router(gpt_4_v3.router)
app.include_router(gpt_5_v2.router)
app.include_router(kkk.router)
app.include_router(grok.router)
app.include_router(deepseek.router)
app.include_router(clean_deepseek.router)
app.include_router(restaurant.router)
app.include_router(restaurant_claude.router)
app.include_router(restaurant_grok.router)
app.include_router(restaurant_gpt5.router)
app.include_router(solar.router)
app.include_router(upload_text.router)
app.include_router(get_ref.router)
app.include_router(chunk.router)
app.include_router(gpt_merge.router)
app.include_router(my.router)
app.include_router(song.router)
app.include_router(gang.router)
app.include_router(step_by_step.router)
app.include_router(clean.router)
app.include_router(mdx_post.router)
app.include_router(synonym.router)
app.include_router(review.router)
app.include_router(news.router)
app.include_router(deep_search.router)
app.include_router(translation_compare.router)
app.include_router(analyzer_router.router)
app.include_router(xai_prompt_engineer.router)
app.include_router(openai_prompt_engineer.router)
app.include_router(story_analysis.router)
app.include_router(requirement_analysis.router)
app.include_router(search_keyword.router)
app.include_router(search_manuscript.router)
app.include_router(search_all.router)
