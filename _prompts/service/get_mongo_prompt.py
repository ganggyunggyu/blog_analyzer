from __future__ import annotations
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from bson import ObjectId
from mongodb_service import MongoDBService
from utils.select_template import select_template


@dataclass
class PromptComponents:
    """프롬프트 구성 요소"""

    subtitles: List[str]
    expressions: Dict[str, List[str]]
    parameters: Dict[str, List[str]]
    template: Optional[Dict[str, Any]]
    template_info: str
    category: str
    keyword: str


class GPT5MongoPromptBuilder:
    """GPT-5에 최적화된 MongoDB 프롬프트 빌더 (Grok 최적화: JSON 중심, 데이터 사용 지침 중심)"""

    def __init__(self, category: str, keyword: str = ""):
        self.category = category
        self.keyword = keyword
        self.db_service = MongoDBService()
        self.db_service.set_db_name(category)

    def get_components(self) -> PromptComponents:
        """MongoDB에서 데이터 추출 및 정제 (inline 처리로 간소화)"""
        analysis_data = self.db_service.get_latest_analysis_data() or {}

        # Inline 데이터 정제
        subtitles = [
            str(item).strip()
            for item in analysis_data.get("subtitles", [])
            if str(item).strip()
        ]
        expressions = {
            str(k): [str(v).strip() for v in (vals or []) if str(v).strip()]
            for k, vals in analysis_data.get("expressions", {}).items()
        }
        parameters = {
            str(k): [str(v).strip() for v in (vals or []) if str(v).strip()]
            for k, vals in analysis_data.get("parameters", {}).items()
        }

        # 템플릿 선택
        template, template_info = self._select_template(
            analysis_data.get("templates", [])
        )

        return PromptComponents(
            subtitles=subtitles,
            expressions=expressions,
            parameters=parameters,
            template=template,
            template_info=template_info,
            category=self.category,
            keyword=self.keyword,
        )

    def _select_template(self, templates: List) -> tuple[Optional[Dict], str]:
        """템플릿 선택 및 정보 추출 (에러 핸들링 강화)"""
        if not templates:
            return None, "템플릿 없음"

        try:
            result = select_template(
                collection=self.db_service.db["templates"],
                templates=templates,
                keyword=self.keyword,
                top_n=3,
            )

            selected = result.get("selected_template")
            if not selected:
                return None, "템플릿 선택 실패"

            file_name = selected.get("file_name", "파일명 없음")
            template_id = str(selected.get("_id", "ID 없음"))
            method = result.get("selection_method", "unknown")

            return selected, f"{file_name}:{template_id} ({method})"
        except Exception as e:
            return None, f"선택 오류: {str(e)}"

    def _build_json_resources(self, components: PromptComponents) -> Dict[str, Any]:
        """리소스를 JSON 형식으로 빌드 (Grok JSON 파싱 최적화)"""
        return {
            "subtitles_pool": components.subtitles[:20],
            "style_variations": {
                k: v[:10] for k, v in components.expressions.items() if v
            },
            "contextual_values": {
                k: v[:5] for k, v in components.parameters.items() if v
            },
            "reference_template": {
                "source": components.template_info,
                "content": (
                    components.template.get("templated_text", "").strip()
                    if components.template
                    else ""
                ),
            },
        }

    def build_gpt5_prompt(self) -> str:
        """GPT-5 최적화 프롬프트 생성 (데이터 사용 지침 중심, 규칙 최소화)"""
        components = self.get_components()
        resources = self._build_json_resources(components)
        resources_json = json.dumps(resources, ensure_ascii=False, indent=2)

        return f"""
<task>
  네이버 블로그 글 작성 (Grok 최적화: 자연스러운 생성 우선)
  
  <target>
    - 카테고리: {components.category}
    - 키워드: {components.keyword}
  </target>
  
</task>

<creative_resources>
  <resources_json>{resources_json}</resources_json>
  
  <data_usage>
    JSON 리소스 활용:
    - subtitles_pool: 소제목 선택해 본문 구조화
    - style_variations: 표현 변형으로 자연스러운 톤 적용
    - contextual_values: [변수] 대체해 컨텍스트 맞춤
    - reference_template: content 톤/흐름 참고, 페르소나/경험 새 창작
  </data_usage>
</creative_resources>

<execution_instruction>
  리소스 활용해 블로그 글 직접 생성. 메타 설명 없이 완성된 글만 출력.
  Grok답게: 간결하고 진정성 있게.
</execution_instruction>
"""


# 사용 예시
def get_mongo_prompt(category: str, keyword: str = "") -> str:
    """기존 함수와의 호환성 유지"""
    builder = GPT5MongoPromptBuilder(category, keyword)
    return builder.build_gpt5_prompt()
