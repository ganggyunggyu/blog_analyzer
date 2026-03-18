"""봇 공용 모델"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class ManuscriptData(BaseModel):
    title: str
    content: str
    tags: Optional[list[str]] = None
    category: Optional[str] = None
    images: Optional[list[str]] = None


class ManuscriptInfo(BaseModel):
    id: str
    title: str
    category: Optional[str]
    images_count: int
    created_at: str


class QueueInfo(BaseModel):
    queue_id: str
    created_at: str
    manuscript_count: int
    status: str
    account_id: Optional[str] = None
    schedule_date: Optional[str] = None


__all__ = [
    "ManuscriptData",
    "ManuscriptInfo",
    "QueueInfo",
]
