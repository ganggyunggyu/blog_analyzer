from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter()


class GenerateGptVer3Request(BaseModel):
    service: str = Field(default="gpt-ver3", description="서비스 식별(로깅용)")
    keyword: str = Field(..., min_length=1, description="생성할 키워드 또는 주제")
    ref: str = Field(default="", description="참조 원고 (스타일 참고용)")


class GenerateGptVer3Response(BaseModel):
    content: str = Field(default="", description="생성된 원고 (현재는 stub)")
    createdAt: datetime = Field(default_factory=datetime.now, description="서버 생성 시각")
    engine: str = Field(default="gpt-ver3", description="엔진 식별자")
    service: str = Field(default="gpt-ver3", description="서비스 식별자")
    keyword: str = Field(..., description="요청 키워드")
    ref: str = Field(default="", description="참조 원고")
    isStub: bool = Field(default=True, description="현재 stub 응답 여부")


@router.post(
    "/generate/gpt-ver3",
    response_model=GenerateGptVer3Response,
    summary="GPT Ver3 (stub)",
    description="프론트 연동을 위해 먼저 열어둔 stub 엔드포인트입니다. 아직 LLM 호출/DB 저장은 없습니다.",
)
async def generate_gpt_ver3(
    request: GenerateGptVer3Request,
) -> GenerateGptVer3Response:
    keyword = (request.keyword or "").strip()
    if not keyword:
        raise HTTPException(status_code=400, detail="keyword는 필수입니다.")

    service = (request.service or "gpt-ver3").strip() or "gpt-ver3"
    ref = request.ref or ""

    return GenerateGptVer3Response(
        content="",
        engine="gpt-ver3",
        service=service,
        keyword=keyword,
        ref=ref,
        isStub=True,
    )
