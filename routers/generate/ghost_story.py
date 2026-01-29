"""괴담 생성 라우터"""

import time
from fastapi import HTTPException, APIRouter
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel
from typing import Optional

from llm.ghost_story_service import generate_ghost_story, MODEL_NAME
from utils.progress_logger import progress
from utils.logger import log


router = APIRouter()


class GhostStoryRequest(BaseModel):
    keyword: str
    setting: Optional[str] = ""
    style: Optional[str] = ""


class GhostStoryResponse(BaseModel):
    content: str
    keyword: str
    setting: str
    style: str
    model: str
    char_count: int
    elapsed: float


@router.post("/generate/ghost-story", response_model=GhostStoryResponse)
async def create_ghost_story(request: GhostStoryRequest):
    """괴담 생성 API

    - keyword: 괴담 주제/키워드 (필수)
    - setting: 배경 설정 (선택)
    - style: 스타일 (선택)
    """
    start_ts = time.time()
    keyword = request.keyword.strip()
    setting = request.setting.strip() if request.setting else ""
    style = request.style.strip() if request.style else ""

    if not keyword:
        raise HTTPException(status_code=400, detail="keyword가 필요합니다.")

    log.header("괴담 생성", "👻")
    log.kv("키워드", keyword)
    log.kv("배경", setting or "기본")
    log.kv("스타일", style or "기본")
    log.kv("모델", MODEL_NAME)

    try:
        with progress(label=f"ghost:{keyword}"):
            result = await run_in_threadpool(
                generate_ghost_story,
                keyword=keyword,
                setting=setting,
                style=style,
            )

        elapsed = time.time() - start_ts

        log.divider()
        log.success("괴담 완료", 키워드=keyword, 길이=f"{result['char_count']}자", 시간=f"{elapsed:.1f}s")

        return GhostStoryResponse(
            content=result["content"],
            keyword=result["keyword"],
            setting=result["setting"],
            style=result["style"],
            model=result["model"],
            char_count=result["char_count"],
            elapsed=round(elapsed, 2),
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"괴담 생성 중 오류: {e}")
