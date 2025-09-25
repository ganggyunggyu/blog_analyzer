from __future__ import annotations
from datetime import datetime
from typing import List, Set
import time
import re

from mongodb_service import MongoDBService


def analyze_morphemes(text: str, category: str = "", file_name: str = "") -> List[str]:
    morphemes_set: Set[str] = set(re.findall(r"[가-힣]{2,}", text))
    morphemes = list(morphemes_set)

    if category:
        db_service = MongoDBService()
        db_service.set_db_name(category)

        now = datetime.now()
        docs_to_save = [
            {
                "timestamp": now,
                "file_name": file_name,
                "db_category": category,
                "category": "morpheme",
                "morpheme": morpheme,
            }
            for morpheme in morphemes
        ]

        if docs_to_save:
            db_service.insert_many_documents("morphemes", docs_to_save)

        print(f"{category}-형태소 분석 완료")
        print(f"추출된 형태소: {len(morphemes)}개")

        db_service.close_connection()

    return morphemes
