from __future__ import annotations
from datetime import datetime
from typing import List
import re

from mongodb_service import MongoDBService


def split_sentences(text: str, category: str = "", file_name: str = "") -> List[str]:
    sentences = re.split(r'(?<=[\.?!다요])\s+', text)
    sentences = [s.strip() for s in sentences if s.strip()]

    if category:
        db_service = MongoDBService()
        db_service.set_db_name(category)

        # MongoDB에 저장
        now = datetime.now()
        docs_to_save = [
            {
                "timestamp": now,
                "file_name": file_name,
                "db_category": category,
                "category": "sentence",
                "sentence": sentence,
            }
            for sentence in sentences
        ]

        if docs_to_save:
            db_service.insert_many_documents("sentences", docs_to_save)

        print(f"{category}-문장 분리 완료")
        print(f"분리된 문장: {len(sentences)}개")

        db_service.close_connection()

    return sentences