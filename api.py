# 표준 라이브러리
import os
import asyncio

# 외부 라이브러리
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 라우터 - 기본
from routers import ingest
from routers.test import test

# 라우터 - 원고 생성
from routers.generate import (
    claude, clean_claude, clean_deepseek, deepseek, deepseek_new,
    gemini_3_pro, gemini_3_flash, gemini_3_flash_clean, gemini_image, gemini_new, gemini_cafe, gemini_cafe_daily,
    gemini_ceo, gpt_ceo,
    gpt4o, chatgpt4o, gpt_ver3_clean, gpt_5_2, kkk,
    grok, grok_new, grok_ver3_clean, keigo, x_illustrator,
    openai_new, solar, solar_ver3_clean,
    batch as generate_batch,
    stream as generate_stream,
    comment as generate_comment,
    recomment as generate_recomment,
    keyword_generator,
    test_comment, test_recomment, test_cafe_daily,
    ghost_story,
    restaurant_gemini,
    update_restaurant,
    cafe_total,
    blog_filler,
    blog_filler_pet,
)

# 라우터 - 분석
from routers.category import keyword
from routers.analysis import get_sub_title, upload_text, analyzer_router
from routers.ref import get_ref

# 라우터 - 원고 관리
from routers.manuscript import visibility as manuscript_visibility

# 라우터 - 검색
from routers.search import (
    keyword as search_keyword, manuscript as search_manuscript,
    all as search_all, autocomplete as search_autocomplete,
    manage as search_manage, popular as search_popular,
    stats as search_stats, history as search_history, bookmark as search_bookmark,
)

# 라우터 - 인증
from routers.auth import naver as auth_naver
from routers.auth import blog_write as auth_blog_write

# 라우터 - 봇
from routers.bot import router as bot_router

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

# 기본
app.include_router(ingest.router)
app.include_router(test.router)

# 원고 생성
app.include_router(claude.router)
app.include_router(clean_claude.router)
app.include_router(deepseek.router)
app.include_router(deepseek_new.router)
app.include_router(clean_deepseek.router)
app.include_router(gemini_3_pro.router)
app.include_router(gemini_3_flash.router)
app.include_router(gemini_3_flash_clean.router)
app.include_router(gemini_image.router)
app.include_router(gemini_new.router)
app.include_router(gemini_cafe.router)
app.include_router(gemini_cafe_daily.router)
app.include_router(gpt4o.router)
app.include_router(chatgpt4o.router)
app.include_router(gpt_ver3_clean.router)
app.include_router(gpt_5_2.router)
app.include_router(gpt_ceo.router)
app.include_router(gemini_ceo.router)
app.include_router(kkk.router)
app.include_router(grok.router)
app.include_router(grok_new.router)
app.include_router(grok_ver3_clean.router)
app.include_router(keigo.router)
app.include_router(x_illustrator.router)
app.include_router(openai_new.router)
app.include_router(solar.router)
app.include_router(solar_ver3_clean.router)
app.include_router(generate_batch.router)
app.include_router(generate_stream.router)
app.include_router(generate_comment.router)
app.include_router(generate_recomment.router)
app.include_router(test_comment.router)
app.include_router(test_recomment.router)
app.include_router(test_cafe_daily.router)
app.include_router(keyword_generator.router)
app.include_router(ghost_story.router)
app.include_router(restaurant_gemini.router)
app.include_router(update_restaurant.router)
app.include_router(cafe_total.router)
app.include_router(blog_filler.router)
app.include_router(blog_filler_pet.router)

# 분석
app.include_router(keyword.router)
app.include_router(get_sub_title.router)
app.include_router(upload_text.router)
app.include_router(get_ref.router)
app.include_router(analyzer_router.router)

# 원고 관리
app.include_router(manuscript_visibility.router)

# 검색
app.include_router(search_keyword.router)
app.include_router(search_manuscript.router)
app.include_router(search_all.router)
app.include_router(search_autocomplete.router)
app.include_router(search_manage.router)
app.include_router(search_popular.router)
app.include_router(search_stats.router)
app.include_router(search_history.router)
app.include_router(search_bookmark.router)

# 인증
app.include_router(auth_naver.router)
app.include_router(auth_blog_write.router)

# 봇
app.include_router(bot_router)
