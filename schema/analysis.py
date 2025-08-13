from typing import List, Dict, Any
from pydantic import BaseModel

class AnalysisData(BaseModel):
    unique_words: List[str] = []
    sentences: List[str] = []
    expressions: Dict[str, Any] = {}
    parameters: Dict[str, Any] = []

    def is_complete(self) -> bool:
        return bool(self.unique_words and self.sentences and self.expressions and self.parameters)