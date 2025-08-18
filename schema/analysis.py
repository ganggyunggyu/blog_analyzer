
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

@dataclass
class AnalysisData:
    unique_words: List[str] = field(default_factory=list)
    sentences: List[str] = field(default_factory=list)
    expressions: Dict[str, List[str]] = field(default_factory=dict)
    parameters: Dict[str, List[str]] = field(default_factory=dict)
    subtitles: List[str] = field(default_factory=list)
    templates: List[Dict[str, Any]] = field(default_factory=list)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "AnalysisData":
        return cls(
            unique_words=list(d.get("unique_words", []) or []),
            sentences=list(d.get("sentences", []) or []),
            expressions=dict(d.get("expressions", {}) or {}),
            parameters=dict(d.get("parameters", {}) or {}),
            subtitles=list(d.get("subtitles", []) or []),
            templates=list(d.get("templates", []) or []),
        )

    def is_complete(self) -> bool:
        # 원고 생성에 필요한 최소 요건 정의 (필요시 조정)
        return bool(self.sentences and self.expressions and self.parameters)