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
<task>
  네이버 블로그 글 작성
  
  <target>
    - 카테고리: {components.category}
    - 키워드: {components.keyword}
  </target>
  
  <structure>
    - 도입부 (3-5줄)
    - 본문: 5가지 주제를 자연스러운 문단 전환으로 서술
      {self._format_subtitles_xml(components.subtitles)}
      
      <structure_note>
        각 주제는 마크다운 헤더(#, ##) 사용 금지.
        대신 "첫째로", "그리고", "또한", "마지막으로" 같은 
        자연스러운 전환어로 단락을 구분하거나,
        "1, 2, 3, 4, 5" 숫자만 간결하게 사용.
        
        절대 금지: *, **, #, ##, •, ▶, →, 리스트 형식
      </structure_note>
    - 맺음말 (2-3줄)
  </structure>
</task>

<creative_resources>
  <style_variations>
    {self._format_expressions_xml(components.expressions)}
  </style_variations>
  
  <contextual_values>
    {self._format_parameters_xml(components.parameters)}
    
    <usage_note>
      템플릿의 [변수]와 고유명사를 컨텍스트에 맞게 자연스럽게 변형하세요.
      예: 33평→28평, A씨→다른 이름, 특정 업체명→컨텍스트 적합 업체명
    </usage_note>
  </contextual_values>
  
  <reference_template>
    <source>{components.template_info}</source>
    
    <how_to_use>
      1. 템플릿의 톤, 흐름, 스토리텔링 방식을 참고
      2. 화자는 템플릿과 다른 새로운 페르소나로 변형
      3. 고유한 경험담과 감정선 창작
      4. [변수]는 컨텍스트에 맞게 대체
      5. 템플릿에 마크다운이나 특수문자가 있어도 절대 따라하지 말 것
    </how_to_use>
    
    <template_content>
      {self._format_template_xml(components.template)}
    </template_content>
  </reference_template>
</creative_resources>

<quality_requirements priority="descending">
  <critical>
    1. 5가지 주제를 자연스러운 산문체로 서술 (마크다운/특수문자 절대 금지)
    2. 키워드 자연스럽게 통합 (억지 삽입 금지)
    3. 상위 프롬프트의 형식 금지 규칙 엄수
  </critical>
  
  <high>
    4. 템플릿과 다른 독창적 페르소나 창작
    5. 템플릿 스타일 참조하되 그대로 복사 금지
  </high>
  
  <medium>
    6. 자연스러운 감정 표현
    7. 실제 사람이 쓴 것 같은 진정성
  </medium>
</quality_requirements>

<formatting_reminder>
  절대 금지:
  - 마크다운 헤더: #, ##, ###
  - 강조 기호: *, **, _
  - 특수 기호: •, ▶, →, ✓, ✔
  - 리스트 형식의 나열
  
  허용:
  - 자연스러운 문단 나누기 (줄바꿈)
  - "첫째", "둘째" 같은 전환어
  - 간결한 숫자 (1, 2, 3)
  - 일반 문장 부호 (.,!?)
</formatting_reminder>

<execution_instruction>
  위 리소스를 활용해 블로그 글을 직접 작성하세요.
  계획이나 과정 설명 없이, 완성된 글만 출력하세요.
  반드시 자연스러운 산문체로 작성하고, 상위 프롬프트의 금지 형식을 절대 사용하지 마세요.
</execution_instruction>
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
