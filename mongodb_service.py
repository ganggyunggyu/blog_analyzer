from pymongo import MongoClient
from config import MONGO_URI, MONGO_DB_NAME

class MongoDBService:
    def __init__(self):
        if not MONGO_URI or not MONGO_DB_NAME:
            raise ValueError("MongoDB URI or DB Name is not configured in .env")
        self.client = MongoClient(MONGO_URI)
        self.db = self.client[MONGO_DB_NAME]

    def insert_document(self, collection_name: str, document: dict):
        """단일 문서를 지정된 컬렉션에 삽입합니다."""
        collection = self.db[collection_name]
        result = collection.insert_one(document)
        return result.inserted_id

    def insert_many_documents(self, collection_name: str, documents: list):
        """여러 문서를 지정된 컬렉션에 삽입합니다."""
        if not documents:
            return []
        collection = self.db[collection_name]
        result = collection.insert_many(documents)
        return result.inserted_ids

    def find_documents(self, collection_name: str, query: dict = None):
        """지정된 컬렉션에서 문서를 조회합니다."""
        collection = self.db[collection_name]
        return list(collection.find(query or {}))

    def update_document(self, collection_name: str, query: dict, new_values: dict):
        """지정된 컬렉션에서 문서를 업데이트합니다."""
        collection = self.db[collection_name]
        result = collection.update_one(query, {"$set": new_values})
        return result.modified_count

    def delete_document(self, collection_name: str, query: dict):
        """지정된 컬렉션에서 문서를 삭제합니다."""
        collection = self.db[collection_name]
        result = collection.delete_one(query)
        return result.deleted_count

    def close_connection(self):
        """MongoDB 연결을 닫습니다."""
        self.client.close()


    def get_latest_analysis_data(self):
        """MongoDB에서 최신 분석 데이터를 가져옵니다."""
        unique_words = []
        sentences = []
        expressions = {}
        parameters = {}

        # 형태소
        morpheme_docs = self.find_documents(collection_name='morphemes')
        if morpheme_docs:
            unique_words = [doc["word"] for doc in morpheme_docs if "word" in doc]
        else:
            unique_words = []

        # 문장
        sentence_docs = self.find_documents(collection_name='sentences')
        if sentence_docs:
            sentences = [doc["sentence"] for doc in sentence_docs if "sentence" in doc]
        else:
            sentences = []

        # 표현
        expression_docs = self.find_documents(
            collection_name='expressions',
        )
        for doc in expression_docs:
            category = doc.get("category")
            expression = doc.get("expression")
            if category and expression:
                expressions.setdefault(category, [])
                if expression not in expressions[category]:
                    expressions[category].append(expression)

        # 파라미터
        parameter_docs = self.find_documents(
            collection_name='parameters',
        )
        for doc in parameter_docs:
            category = doc.get("category")
            parameter = doc.get("parameter")
            if category and parameter:
                parameters.setdefault(category, [])
                if parameter not in parameters[category]:
                    parameters[category].append(parameter)

        return {
            "unique_words": unique_words,
            "sentences": sentences,
            "expressions": expressions,
            "parameters": parameters
        }
    def set_db_name(self, db_name: str):
        """MongoDB의 데이터베이스 이름을 변경합니다."""
        if not db_name:
            raise ValueError("새 DB 이름은 비어 있을 수 없습니다.")
        self.db = self.client[db_name]