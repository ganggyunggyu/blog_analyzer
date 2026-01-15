"""키워드-카테고리 매핑 생성 라우터"""

from fastapi import APIRouter, HTTPException
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, Field


router = APIRouter()


class KeywordGeneratorRequest(BaseModel):
    """키워드 생성 요청 스키마"""

    categories: list[str] = Field(..., description="사용 가능한 카테고리 목록")
    count: int = Field(default=60, description="생성할 키워드 개수")
    include_keywords: list[str] | None = Field(default=None, description="포함해야 할 키워드 목록")
    exclude_keywords: list[str] | None = Field(default=None, description="제외해야 할 키워드 목록")
    shuffle: bool = Field(default=True, description="카테고리 뒤죽박죽 섞기")
    note: str = Field(default="", description="추가 요청사항")


class KeywordItem(BaseModel):
    """키워드 아이템"""

    keyword: str
    category: str


class KeywordGeneratorResponse(BaseModel):
    """키워드 생성 응답 스키마"""

    keywords: list[KeywordItem]
    count: int
    model: str


@router.post("/keyword-generator", response_model=KeywordGeneratorResponse)
async def generate_keywords_endpoint(request: KeywordGeneratorRequest):
    """키워드-카테고리 매핑 생성 API

    커뮤니티/게시판용 키워드:카테고리 데이터를 생성합니다.

    - **categories**: 사용 가능한 카테고리 목록 (필수)
    - **count**: 생성할 키워드 개수 (기본 60)
    - **include_keywords**: 포함해야 할 키워드 목록
    - **exclude_keywords**: 제외해야 할 키워드 목록
    - **shuffle**: 카테고리 뒤죽박죽 섞기 (기본 True)
    - **note**: 추가 요청사항
    """
    from llm.keyword_generator_service import generate_keywords

    try:
        result = await run_in_threadpool(
            generate_keywords,
            categories=request.categories,
            count=request.count,
            include_keywords=request.include_keywords,
            exclude_keywords=request.exclude_keywords,
            shuffle=request.shuffle,
            note=request.note,
        )

        return KeywordGeneratorResponse(
            keywords=[KeywordItem(**k) for k in result["keywords"]],
            count=result["count"],
            model=result["model"],
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"키워드 생성 실패: {e}")
