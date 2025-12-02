"""UI 데이터 모델"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

__all__ = ["HistoryItem"]


@dataclass
class HistoryItem:
    """히스토리 아이템 데이터"""

    keyword: str
    category: str
    engine: str
    content: str
    created_at: datetime
