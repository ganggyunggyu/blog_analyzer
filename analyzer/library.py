from __future__ import annotations
from datetime import datetime
from typing import Dict, List
from pathlib import Path
import kss

from mongodb_service import MongoDBService


def build_sentence_library(directory_path: str, category: str = "") -> Dict[str, List[str]]:
    library: Dict[str, List[str]] = {}
    p = Path(directory_path)

    if category:
        db_service = MongoDBService()
        db_service.set_db_name(category)

    for file_path in p.glob('*.txt'):
        file_category = file_path.stem

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        sentences = kss.split_sentences(content)

        if file_category not in library:
            library[file_category] = []
        library[file_category].extend(sentences)

        # MongoDB에 저장
        if category:
            now = datetime.now()
            docs_to_save = [
                {
                    "timestamp": now,
                    "file_name": file_path.name,
                    "db_category": category,
                    "category": "sentence_library",
                    "library_category": file_category,
                    "sentence": sentence,
                }
                for sentence in sentences
            ]

            if docs_to_save:
                db_service.insert_many_documents("sentence_library", docs_to_save)

    if category:
        total_sentences = sum(len(sentences) for sentences in library.values())
        print(f"{category}-문장 라이브러리 구축 완료")
        print(f"총 문장 수: {total_sentences}개")
        db_service.close_connection()

    return library
