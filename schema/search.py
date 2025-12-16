from typing import Optional, List
from pydantic import BaseModel, Field


class KeywordSearchRequest(BaseModel):
    query: str = Field(..., description="검색할 키워드")
    category: Optional[str] = Field(None, description="카테고리 필터 (DB명)")
    page: int = Field(1, ge=1, description="페이지 번호")
    limit: int = Field(20, ge=1, le=100, description="페이지당 결과 수")


class SearchRequest(BaseModel):
    q: str = Field(..., description="검색 키워드")
    limit: int = Field(20, ge=1, le=100, description="결과 수 제한")


class SearchFilters(BaseModel):
    dateFrom: Optional[str] = Field(None, description="시작 날짜 (YYYY-MM-DD)")
    dateTo: Optional[str] = Field(None, description="종료 날짜 (YYYY-MM-DD)")
    engine: Optional[List[str]] = Field(None, description="AI 엔진 필터")
    hasRef: Optional[bool] = Field(None, description="참조원고 유무")
    minLength: Optional[int] = Field(None, description="최소 글자수")


class SearchSort(BaseModel):
    field: str = Field("createdAt", description="정렬 필드")
    order: str = Field("desc", description="정렬 순서 (asc/desc)")


class AdvancedSearchRequest(BaseModel):
    query: str = Field(..., description="검색할 키워드")
    category: Optional[str] = Field(None, description="카테고리 필터 (DB명)")
    filters: Optional[SearchFilters] = Field(None, description="검색 필터")
    sort: Optional[SearchSort] = Field(None, description="정렬 옵션")
    page: int = Field(1, ge=1, description="페이지 번호")
    limit: int = Field(20, ge=1, le=100, description="페이지당 결과 수")


class ManuscriptUpdateRequest(BaseModel):
    content: str = Field(..., description="수정된 원고 내용")
    memo: Optional[str] = Field(None, description="수정 메모")


class SearchHistoryRequest(BaseModel):
    keyword: str = Field(..., description="검색어")
    category: Optional[str] = Field(None, description="카테고리")
