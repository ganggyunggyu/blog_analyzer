"""배치 원고 생성 API - 키워드 여러개 한번에 처리"""

import asyncio
import time
from datetime import datetime
from pathlib import Path
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from fastapi.concurrency import run_in_threadpool

from schema.generate import BatchGenerateRequest
from llm.gpt4o_service import gpt4o_gen
from utils.get_category_db_name import get_category_db_name
from utils.logger import log

router = APIRouter()

# pending 폴더 경로
MANUSCRIPTS_DIR = Path("manuscripts")
PENDING_DIR = MANUSCRIPTS_DIR / "pending"
PENDING_DIR.mkdir(parents=True, exist_ok=True)


def get_next_manuscript_id() -> str:
    """다음 원고 ID 생성"""
    existing = list(PENDING_DIR.iterdir()) if PENDING_DIR.exists() else []
    max_id = 0
    for folder in existing:
        if folder.is_dir() and folder.name.isdigit():
            max_id = max(max_id, int(folder.name))
    return str(max_id + 1).zfill(4)


def save_to_pending(keyword: str, content: str) -> str:
    """생성된 원고를 pending 폴더에 저장"""
    manuscript_id = get_next_manuscript_id()
    manuscript_dir = PENDING_DIR / manuscript_id
    manuscript_dir.mkdir(parents=True, exist_ok=True)

    # 첫 줄 = 제목 (키워드 기반), 나머지 = 본문
    title = content.split('\n')[0].strip() if content else keyword

    # txt 파일로 저장
    txt_path = manuscript_dir / f"{keyword[:20]}.txt"
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(content)

    return manuscript_id


@router.post("/generate/batch")
async def generate_batch(request: BatchGenerateRequest):
    """
    배치 원고 생성 - 키워드 여러개 한번에 처리
    생성된 원고는 자동으로 pending 폴더에 저장
    """
    start_ts = time.time()
    service = request.service.lower()
    keywords = request.keywords
    ref = request.ref

    log.header(f"배치 원고 생성 시작", "📦")
    log.kv("서비스", service.upper())
    log.kv("키워드 수", len(keywords))

    results = []
    success_count = 0

    for idx, keyword in enumerate(keywords):
        keyword = keyword.strip()
        if not keyword:
            continue

        log.step(idx + 1, len(keywords), keyword[:30])

        try:
            # 카테고리 분류
            category = await get_category_db_name(keyword=keyword + ref)

            # 원고 생성
            content = await run_in_threadpool(
                gpt4o_gen,
                user_instructions=keyword,
                ref=ref,
                category=category
            )

            if content:
                # pending 폴더에 저장
                manuscript_id = save_to_pending(keyword, content)
                success_count += 1

                results.append({
                    "keyword": keyword,
                    "success": True,
                    "manuscript_id": manuscript_id,
                    "length": len(content),
                })
                log.success(f"생성 완료", keyword=keyword[:20], id=manuscript_id)
            else:
                results.append({
                    "keyword": keyword,
                    "success": False,
                    "message": "생성 실패",
                })
                log.error(f"생성 실패", keyword=keyword[:20])

        except Exception as e:
            results.append({
                "keyword": keyword,
                "success": False,
                "message": str(e),
            })
            log.error(f"에러", keyword=keyword[:20], error=str(e))

        # 요청 간 딜레이 (API 부하 방지)
        if idx < len(keywords) - 1:
            await asyncio.sleep(1)

    elapsed = time.time() - start_ts
    log.divider()
    log.success(f"배치 완료", 성공=f"{success_count}/{len(keywords)}", 시간=f"{elapsed:.1f}s")

    return JSONResponse(content={
        "total": len(keywords),
        "success": success_count,
        "failed": len(keywords) - success_count,
        "elapsed": round(elapsed, 1),
        "results": results,
    })
