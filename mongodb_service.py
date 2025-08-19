# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TypedDict, List, Dict, Any, Optional, Tuple, Union
from datetime import datetime

from pymongo import MongoClient, ASCENDING
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.errors import BulkWriteError, DuplicateKeyError

from config import MONGO_URI, MONGO_DB_NAME
# -----------------------
# 1) 스키마 (자동완성/타입힌트)
# -----------------------
class MorphemeDoc(TypedDict, total=False):
    _id: Any
    timestamp: float
    word: str

class SentenceDoc(TypedDict, total=False):
    _id: Any
    timestamp: float
    sentence: str

class ExpressionDoc(TypedDict, total=False):
    _id: Any
    timestamp: float
    category: str
    expression: str

class ParameterDoc(TypedDict, total=False):
    _id: Any
    timestamp: float
    category: str
    parameter: str

class SubtitleDoc(TypedDict, total=False):
    _id: Any
    timestamp: float
    subtitles: List[str]

class TemplateDoc(TypedDict, total=False):
    _id: Any
    timestamp: datetime
    file_name: Optional[str]
    templated_text: str


# -----------------------
# 2) 인덱스 정의
#    - 단일 필드 유니크
#    - 복합(카테고리+값) 유니크
# -----------------------
UniqueIndex = Union[str, List[Tuple[str, int]]]

INDEX_MAP: Dict[str, UniqueIndex] = {
    # 컬렉션  → 유니크 인덱스
    "morphemes": "word",                               # word
    "sentences": "sentence",                           # sentence
    "expressions": [("category", ASCENDING),
                    ("expression", ASCENDING)],        # (category, expression)
    "parameters": [("category", ASCENDING),
                   ("parameter", ASCENDING)],          # (category, parameter)
    # "subtitles": ???   # 일반적으로 중복 허용
    # "templates": ???   # 일반적으로 중복 허용
}

class MongoDBService:
    def __init__(self):
        if not MONGO_URI or not MONGO_DB_NAME:
            raise ValueError("MongoDB URI or DB Name is not configured in .env")
        self.client: MongoClient = MongoClient(MONGO_URI)
        self.db: Database = self.client[MONGO_DB_NAME]

    # ---------------------------
    # 기본 CRUD
    # ---------------------------
    def insert_document(self, collection_name: str, document: dict):
        """단일 문서를 지정된 컬렉션에 삽입합니다."""
        return self.db[collection_name].insert_one(document).inserted_id

    def insert_many_documents(self, collection_name: str, documents: List[dict]):
        """여러 문서를 지정된 컬렉션에 삽입합니다. 
        - 중복 키가 있으면 무시하고 넘어감
        """
        if not documents:
            return []

        try:
            result = self.db[collection_name].insert_many(
                documents, ordered=False
            )
            return result.inserted_ids
        except BulkWriteError as e:
            # 중복키 오류만 무시하고 나머지는 그대로 raise
            write_errors = [err for err in e.details.get("writeErrors", []) if err.get("code") != 11000]
            if write_errors:
                raise  # 중복 외 에러는 터뜨림
            # 중복 발생 시, 성공한 inserted_ids만 반환
            return e.details.get("nInserted", 0)

    def find_documents(self, collection_name: str, query: Optional[dict] = None) -> List[dict]:
        """지정된 컬렉션에서 문서를 조회합니다."""
        return list(self.db[collection_name].find(query or {}))

    def update_document(self, collection_name: str, query: dict, new_values: dict) -> int:
        """지정된 컬렉션에서 문서를 업데이트합니다."""
        result = self.db[collection_name].update_one(query, {"$set": new_values})
        return result.modified_count

    def delete_document(self, collection_name: str, query: dict) -> int:
        """지정된 컬렉션에서 문서를 삭제합니다."""
        result = self.db[collection_name].delete_one(query)
        return result.deleted_count

    def close_connection(self):
        """MongoDB 연결을 닫습니다."""
        self.client.close()

    def set_db_name(self, db_name: str):
        """MongoDB의 데이터베이스 이름을 변경합니다."""
        if not db_name:
            raise ValueError("새 DB 이름은 비어 있을 수 없습니다.")
        self.db = self.client[db_name]
            

    # ---------------------------
    # 분석 데이터 수집
    # ---------------------------
    def get_latest_analysis_data(self) -> Dict[str, Any]:
        """
        MongoDB에서 최신 분석 데이터를 모아 반환합니다.
        반환 스키마:
        {
          "unique_words": List[str],
          "sentences": List[str],
          "expressions": Dict[str, List[str]],
          "parameters": Dict[str, List[str]],
          "subtitles": List[str],
          "templates": List[{"file_name": Optional[str], "templated_text": str}]
        }
        """
        unique_words: List[str] = []
        sentences: List[str] = []
        expressions: Dict[str, List[str]] = {}
        parameters: Dict[str, List[str]] = {}
        subtitles: List[str] = []
        templates: List[Dict[str, Any]] = []

        # 형태소
        for doc in self.find_documents("morphemes"):
            w = doc.get("word")
            if isinstance(w, str) and w:
                unique_words.append(w)

        # 문장
        for doc in self.find_documents("sentences"):
            s = doc.get("sentence")
            if isinstance(s, str) and s:
                sentences.append(s)

        # 표현 (카테고리별 중복 제거)
        for doc in self.find_documents("expressions"):
            cat = doc.get("category")
            expr = doc.get("expression")
            if isinstance(cat, str) and cat and isinstance(expr, str) and expr:
                expressions.setdefault(cat, [])
                if expr not in expressions[cat]:
                    expressions[cat].append(expr)

        # 파라미터 (카테고리별 중복 제거)
        for doc in self.find_documents("parameters"):
            cat = doc.get("category")
            par = doc.get("parameter")
            if isinstance(cat, str) and cat and isinstance(par, str) and par:
                parameters.setdefault(cat, [])
                if par not in parameters[cat]:
                    parameters[cat].append(par)

        # 부제(subtitles): 문서마다 ["subtitles"] 배열을 합침
        for doc in self.find_documents("subtitles"):
            arr = doc.get("subtitles")
            if isinstance(arr, list):
                for s in arr:
                    if isinstance(s, str) and s.strip():
                        subtitles.append(s.strip())

        # 템플릿(templates): templated_text만 수집 (file_name 있으면 함께 보관)
        for doc in self.find_documents("templates"):
            tt = doc.get("templated_text")
            if isinstance(tt, str) and tt.strip():
                templates.append({
                    "file_name": doc.get("file_name"),  # 없을 수 있음
                    "templated_text": tt.strip()
                })

        return {
            "unique_words": unique_words,
            "sentences": sentences,
            "expressions": expressions,
            "parameters": parameters,
            "subtitles": subtitles,
            "templates": templates,
        }