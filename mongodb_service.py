from __future__ import annotations

from typing import TypedDict, List, Dict, Any, Optional, Tuple, Union
from datetime import datetime

from pymongo import MongoClient, ASCENDING, UpdateOne
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.errors import BulkWriteError, DuplicateKeyError

from config import MONGO_URI, MONGO_DB_NAME


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


UniqueIndex = Union[str, List[Tuple[str, int]]]

# 유니크 인덱스 정의: 없으면 생성
INDEX_MAP: Dict[str, UniqueIndex] = {
    "morphemes": "word",
    "sentences": "sentence",
    "expressions": [("category", ASCENDING), ("expression", ASCENDING)],
    "parameters": [("category", ASCENDING), ("parameter", ASCENDING)],
    "templates": "file_name",
}


def _to_index_tuple(x: UniqueIndex) -> List[Tuple[str, int]]:
    if isinstance(x, str):
        return [(x, ASCENDING)]
    return list(x)


class MongoDBService:
    def __init__(self):
        if not MONGO_URI or not MONGO_DB_NAME:
            raise ValueError("MongoDB URI or DB Name is not configured in .env")
        self.client: MongoClient = MongoClient(MONGO_URI)
        self.db: Database = self.client[MONGO_DB_NAME]
        self.ensure_unique_indexes()

    # ---------- 인덱스 ----------
    def ensure_unique_indexes(self) -> None:
        """
        INDEX_MAP 기준으로 유니크 인덱스 보장.
        이미 있으면 패스.
        """
        for coll_name, spec in INDEX_MAP.items():
            idx_fields = _to_index_tuple(spec)
            try:
                self.db[coll_name].create_index(
                    idx_fields,
                    unique=True,
                    name="uniq_" + "_".join(k for k, _ in idx_fields),
                )
            except Exception:
                # 이미 존재/경쟁 생성 등은 조용히 스킵
                pass

    # ---------- 쓰기(중복 안전) ----------
    def insert_document(self, collection_name: str, document: dict):
        """
        단건 삽입 (유니크 인덱스 위반 시 DuplicateKeyError 발생 가능)
        -> 가급적 upsert_document 사용 권장
        """
        return self.db[collection_name].insert_one(document).inserted_id

    def upsert_document(
        self, collection_name: str, key: Dict[str, Any], doc: Dict[str, Any]
    ) -> bool:
        """
        key로 존재 여부 판단 후 없으면 삽입. 있으면 그대로 유지 (idempotent).
        반환: True(새로 생성됨) / False(이미 존재)
        """
        res = self.db[collection_name].update_one(
            key, {"$setOnInsert": doc}, upsert=True
        )
        return res.upserted_id is not None

    def insert_many_documents(self, collection_name: str, documents: List[dict]):
        """
        여러 문서를 삽입. 유니크 위반은 무시하고 진행.
        (기존 동작 유지)
        """
        if not documents:
            return []

        try:
            result = self.db[collection_name].insert_many(documents, ordered=False)
            return result.inserted_ids
        except BulkWriteError as e:
            write_errors = [
                err
                for err in e.details.get("writeErrors", [])
                if err.get("code") != 11000
            ]
            if write_errors:
                raise
            return e.details.get("nInserted", 0)

    def upsert_many_documents(
        self, collection_name: str, documents: List[dict], key_fields: List[str]
    ) -> Dict[str, int]:
        """
        벌크 업서트: key_fields 조합으로 중복 차단. 전체 원자성은 없지만 각 연산은 원자적.
        반환 요약: {"upserted": n, "matched": n2}
        """
        if not documents:
            return {"upserted": 0, "matched": 0}

        ops: List[UpdateOne] = []
        for d in documents:
            key = {k: d.get(k) for k in key_fields}
            ops.append(UpdateOne(key, {"$setOnInsert": d}, upsert=True))

        res = self.db[collection_name].bulk_write(ops, ordered=False)
        return {"upserted": res.upserted_count, "matched": res.matched_count}

    # ---------- 읽기/수정/삭제 ----------
    def find_documents(
        self, collection_name: str, query: Optional[dict] = None
    ) -> List[dict]:
        return list(self.db[collection_name].find(query or {}))

    def update_document(
        self, collection_name: str, query: dict, new_values: dict
    ) -> int:
        result = self.db[collection_name].update_one(query, {"$set": new_values})
        return result.modified_count

    def delete_document(self, collection_name: str, query: dict) -> int:
        result = self.db[collection_name].delete_one(query)
        return result.deleted_count

    def close_connection(self):
        self.client.close()

    def set_db_name(self, db_name: str):
        if not db_name:
            raise ValueError("새 DB 이름은 비어 있을 수 없습니다.")
        self.db = self.client[db_name]
        self.ensure_unique_indexes()  # DB 바꾸면 다시 보장

    # ---------- 분석 데이터 수집(빠르고 깨끗하게) ----------
    def get_latest_analysis_data(self) -> Dict[str, Any]:
        """
        반환 스키마:
        {
          "unique_words": List[str],
          "sentences": List[str],
          "expressions": Dict[str, List[str]],
          "parameters": Dict[str, List[str]],
          "subtitles": List[str],
          "templates": List[{"file_name": Optional[str], "templated_text": str}]
        }
        - distinct / aggregation으로 중복 제거 및 속도 개선
        - _id/timestamp 등 불필요 필드 제외
        """

        # morphemes: 단어 고유 집합
        unique_words: List[str] = list(
            self.db["morphemes"].distinct(
                "word", {"word": {"$type": "string", "$ne": ""}}
            )
        )

        # sentences: 문장 고유 집합
        sentences: List[str] = list(
            self.db["sentences"].distinct(
                "sentence", {"sentence": {"$type": "string", "$ne": ""}}
            )
        )

        # expressions: 카테고리별 표현 집합
        expr_map: Dict[str, List[str]] = {}
        expr_pipeline = [
            {
                "$match": {
                    "category": {"$type": "string", "$ne": ""},
                    "expression": {"$type": "string", "$ne": ""},
                }
            },
            {
                "$group": {
                    "_id": "$category",
                    "expressions": {"$addToSet": "$expression"},
                }
            },
        ]
        for row in self.db["expressions"].aggregate(expr_pipeline):
            expr_map[row["_id"]] = sorted(row.get("expressions", []))

        # parameters: 카테고리별 파라미터 집합
        param_map: Dict[str, List[str]] = {}
        par_pipeline = [
            {
                "$match": {
                    "category": {"$type": "string", "$ne": ""},
                    "parameter": {"$type": "string", "$ne": ""},
                }
            },
            {"$group": {"_id": "$category", "parameters": {"$addToSet": "$parameter"}}},
        ]
        for row in self.db["parameters"].aggregate(par_pipeline):
            param_map[row["_id"]] = sorted(row.get("parameters", []))

        # subtitles: 배열 필드 평탄화 후 고유 집합
        subtitles: List[str] = []
        sub_pipeline = [
            {"$project": {"subtitles": 1}},
            {"$unwind": "$subtitles"},
            {"$match": {"subtitles": {"$type": "string", "$ne": ""}}},
            {"$group": {"_id": None, "subs": {"$addToSet": "$subtitles"}}},
        ]
        sub_res = list(self.db["subtitles"].aggregate(sub_pipeline))
        if sub_res:
            subtitles = sorted(sub_res[0].get("subs", []))

        # templates: 필요한 필드만 (_id도 포함)
        templates: List[Dict[str, Any]] = []
        for doc in self.db["templates"].find(
            {}, {"_id": 1, "file_name": 1, "templated_text": 1}
        ):
            tt = (doc.get("templated_text") or "").strip()
            if tt:
                templates.append(
                    {
                        "_id": str(doc.get("_id")) if doc.get("_id") else None,
                        "file_name": doc.get("file_name"),
                        "templated_text": tt
                    }
                )

        return {
            "unique_words": unique_words,
            "sentences": sentences,
            "expressions": expr_map,
            "parameters": param_map,
            "subtitles": subtitles,
            "templates": templates,
        }
