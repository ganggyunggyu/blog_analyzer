from pydantic import BaseModel
from typing import Optional


class GenerateRequest(BaseModel):
    service: str
    keyword: str
    ref: Optional[str] = None