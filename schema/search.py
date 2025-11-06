from typing import Optional
from pydantic import BaseModel, Field


class KeywordSearchRequest(BaseModel):
    query: str = Field(..., description="검색할 키워드")
    category: Optional[str] = Field(None, description="카테고리 필터 (선택)")
    page: int = Field(1, ge=1, description="페이지 번호")
    limit: int = Field(20, ge=1, le=100, description="페이지당 결과 수")
