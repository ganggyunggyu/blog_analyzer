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
    """GPT-5에 최적화된 MongoDB 프롬프트 빌더"""

    def __init__(self, category: str, keyword: str = ""):
        self.category = category
        self.keyword = keyword
        self.db_service = MongoDBService()
        self.db_service.set_db_name(category)

    def get_components(self) -> PromptComponents:
        """MongoDB에서 데이터 추출 및 정제"""
        analysis_data = self.db_service.get_latest_analysis_data() or {}

        # 데이터 추출 및 정제
        subtitles = self._clean_list(analysis_data.get("subtitles", []))
        expressions = self._clean_dict(analysis_data.get("expressions", {}))
        parameters = self._clean_dict(analysis_data.get("parameters", {}))

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

    def _clean_list(self, data: List) -> List[str]:
        """리스트 데이터 정제"""
        return [str(item).strip() for item in data if str(item).strip()]

    def _clean_dict(self, data: Dict) -> Dict[str, List[str]]:
        """딕셔너리 데이터 정제"""
        return {
            str(k): [str(v).strip() for v in (vals or []) if str(v).strip()]
            for k, vals in data.items()
        }

    def _select_template(self, templates: List) -> tuple[Optional[Dict], str]:
        """템플릿 선택 및 정보 추출"""
        if not templates:
            return None, "템플릿 없음"

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

    def build_gpt5_prompt(self) -> str:
        """GPT-5 최적화 프롬프트 생성"""
        components = self.get_components()

        return f"""
<writing_context>
    <metadata>
        <category>{components.category}</category>
        <keyword>{components.keyword}</keyword>
        <output_length min="2200" max="2400" unit="chars_excluding_spaces"/>
    </metadata>
    
    <structure_requirements>
        <format>
            <introduction lines="3-5"/>
            <main_content>
                <subtitle count="5" numbering="required">
                    {self._format_subtitles_xml(components.subtitles)}
                </subtitle>
            </main_content>
            <conclusion lines="2-3"/>
        </format>
    </structure_requirements>
    
    <writing_resources>
        <expressions purpose="style_variation">
            {self._format_expressions_xml(components.expressions)}
        </expressions>
        
        <parameters purpose="value_substitution">
            {self._format_parameters_xml(components.parameters)}
            <substitution_rules>
                <rule>수치 변경: 33평→28평, 60L→90L</rule>
                <rule>이름 변경: A씨→F씨, 원본명→반찬</rule>
                <rule>애견 업체: 모두 "도그마루" 사용</rule>
            </substitution_rules>
        </parameters>
        
        <template_reference>
            <source>{components.template_info}</source>
            <usage_guidelines>
                <variable_handling>
                    - [변수] → 컨텍스트 적합 값으로 대체
                </variable_handling>
                <persona_creation>
                    - 템플릿 화자 분석 후 다른 페르소나 생성
                    - 생성 된 페르소나를 이용한 창의적 스토리텔링 필수
                </persona_creation>
            </usage_guidelines>
            <content>
                {self._format_template_xml(components.template)}
            </content>
        </template_reference>
    </writing_resources>
    
    <quality_criteria priority="ordered">
        <must_have>
            1. 5개 소제목 구조 준수
            3. 키워드 자연스러운 통합
        </must_have>
        <should_have>
            4. 독창적 페르소나
            5. 자연스러운 감정 표현
            6. 템플릿 스타일 참조
        </should_have>
    </quality_criteria>
</writing_context>
"""

    def _format_subtitles_xml(self, subtitles: List[str]) -> str:
        """소제목을 XML 형식으로 변환"""
        if not subtitles:
            return "<pool>소제목 풀 비어있음</pool>"

        items = "\n".join(f"        <option>{s}</option>" for s in subtitles[:20])
        return f"<pool>\n{items}\n    </pool>"

    def _format_expressions_xml(self, expressions: Dict[str, List[str]]) -> str:
        """표현을 XML 형식으로 변환"""
        if not expressions:
            return "<empty/>"

        xml_parts = []
        for category, items in expressions.items():
            if items:
                values = "".join(f"<value>{v}</value>" for v in items[:10])
                xml_parts.append(f'<category name="{category}">{values}</category>')

        return "\n            ".join(xml_parts) if xml_parts else "<empty/>"

    def _format_parameters_xml(self, parameters: Dict[str, List[str]]) -> str:
        """파라미터를 XML 형식으로 변환"""
        if not parameters:
            return "<empty/>"

        xml_parts = []
        for param_type, values in parameters.items():
            if values:
                examples = "".join(f"<example>{v}</example>" for v in values[:5])
                xml_parts.append(f'<type name="{param_type}">{examples}</type>')

        return "\n            ".join(xml_parts) if xml_parts else "<empty/>"

    def _format_template_xml(self, template: Optional[Dict]) -> str:
        """템플릿을 XML 형식으로 변환"""

        if not template:
            return "<empty/>"

        # 템플릿 내용 정제
        content = template.get("templated_text", "")
        if isinstance(content, str):
            # 줄바꿈 유지하되 과도한 공백 제거
            content = "\n".join(line.strip() for line in content.split("\n"))

        return f"<template_text><![CDATA[{content}]]></template_text>"


# 사용 예시
def get_mongo_prompt(category: str, keyword: str = "") -> str:
    """기존 함수와의 호환성 유지"""
    builder = GPT5MongoPromptBuilder(category, keyword)
    return builder.build_gpt5_prompt()
