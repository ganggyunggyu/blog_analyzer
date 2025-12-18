from typing import Optional, List
from pydantic import BaseModel


class GenerateRequest(BaseModel):
    service: str
    keyword: str
    ref: str = ""


class ImageGenerateRequest(BaseModel):
    keyword: str


class ImageItem(BaseModel):
    url: str


class ImageGenerateResponse(BaseModel):
    images: List[ImageItem]
    total: int
    failed: int = 0
