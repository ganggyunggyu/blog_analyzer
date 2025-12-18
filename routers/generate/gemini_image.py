"""Gemini 2.5 Flash - 이미지 5장 생성 라우터"""

import time
from fastapi import HTTPException, APIRouter
from fastapi.concurrency import run_in_threadpool

from schema.generate import ImageGenerateRequest, ImageGenerateResponse, ImageItem
from llm.gemini_image_service import gemini_image_gen, MODEL_NAME, IMAGE_COUNT
from utils.progress_logger import progress


router = APIRouter()


@router.post("/generate/image", response_model=ImageGenerateResponse)
async def generate_image(request: ImageGenerateRequest):
    """
    Gemini 2.5 Flash - 이미지 5장 동시 생성

    - keyword: 이미지 주제 키워드
    """
    start_ts = time.time()
    keyword = request.keyword.strip()

    if not keyword:
        raise HTTPException(status_code=400, detail="keyword가 필요합니다.")

    print("\n" + "=" * 60)
    print(f"IMAGE {IMAGE_COUNT}장 생성 시작")
    print("=" * 60)
    print(f"키워드    : {keyword}")
    print(f"모델      : {MODEL_NAME}")
    print(f"생성 개수 : {IMAGE_COUNT}장")
    print("=" * 60 + "\n")

    try:
        with progress(label=f"image:{keyword}"):
            images, failed_count = await run_in_threadpool(
                gemini_image_gen,
                keyword=keyword,
            )

        elapsed = time.time() - start_ts

        print("\n" + "=" * 60)
        print(f"IMAGE 생성 완료")
        print("=" * 60)
        print(f"키워드       : {keyword}")
        print(f"성공         : {len(images)}장")
        print(f"실패         : {failed_count}장")
        print(f"소요시간     : {elapsed:.2f}s")
        print("=" * 60 + "\n")

        image_items = [
            ImageItem(url=img["url"])
            for img in images
            if img.get("url")
        ]

        return ImageGenerateResponse(
            images=image_items,
            total=len(images),
            failed=failed_count,
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"이미지 생성 중 오류 발생: {e}",
        )
