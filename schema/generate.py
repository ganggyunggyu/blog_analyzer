from typing import Optional
from pydantic import BaseModel


class GenerateRequest(BaseModel):
    service: str
    keyword: str
    ref: str = ""
