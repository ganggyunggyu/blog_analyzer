# 네이버 블로그 SEO 글쓰기 GPT-5 XML 태그 체계

## 📋 목차

1. [최상위 작업 정의](#1-최상위-작업-정의)
2. [SEO 최적화](#2-seo-최적화)
3. [콘텐츠 구조](#3-콘텐츠-구조)
4. [톤 & 스타일](#4-톤--스타일)
5. [데이터 소스](#5-데이터-소스)
6. [품질 관리](#6-품질-관리)
7. [제약사항](#7-제약사항)
8. [특수 기능](#8-특수-기능)
9. [통합 구현 예시](#9-통합-구현-예시)

---

## 1. 최상위 작업 정의

### 작업 메타데이터

```xml
<naver_blog_task>
    <task_metadata>
        <service_type>네이버 블로그 SEO 최적화</service_type>
        <creation_date>{날짜}</creation_date>
        <version>1.0</version>
    </task_metadata>
</naver_blog_task>
```

### 자기 성찰 (GPT-5 특수 기능)

```xml
<self_reflection>
    네이버 블로그 상위노출 기준 체크리스트:
    1. 키워드 최적화 - 자연스러운 키워드 배치
    2. 사용자 체류시간 - 흥미로운 콘텐츠 구성
    3. 정보 신뢰도 - 정확하고 유용한 정보
    4. 모바일 가독성 - 적절한 줄바꿈과 문단
    5. 네이버 정책 준수 - 스팸 방지 정책 준수
</self_reflection>
```

---

## 2. SEO 최적화

### SEO 전략 정의

```xml
<seo_optimization>
    <target_platform>naver</target_platform>
    <ranking_factors>
        <keyword_density min="3%" max="5%"/>
        <content_freshness>최신 트렌드 반영</content_freshness>
        <user_engagement>체류시간 증대 전략</user_engagement>
        <mobile_optimization>모바일 최적화 필수</mobile_optimization>
    </ranking_factors>
</seo_optimization>
```

### 키워드 전략

```xml
<keyword_strategy>
    <primary_keyword frequency="high">{메인 키워드}</primary_keyword>
    <secondary_keywords>
        <keyword relevance="high">{서브 키워드1}</keyword>
        <keyword relevance="medium">{서브 키워드2}</keyword>
        <keyword relevance="low">{서브 키워드3}</keyword>
    </secondary_keywords>
    <lsi_keywords>{연관 검색어 리스트}</lsi_keywords>
    <trending_keywords source="naver_datalab">{실시간 트렌드}</trending_keywords>
</keyword_strategy>
```

### 네이버 특화 요소

```xml
<naver_specific>
    <di_optimization>D.I.A(Document Information Architecture) 최적화</di_optimization>
    <main_keyword_placement>제목, 첫문단, 소제목 필수 포함</main_keyword_placement>
    <view_tab_optimization>View 탭 노출 최적화</view_tab_optimization>
    <smart_block_prevention>스마트블록 회피 전략</smart_block_prevention>
    <c_rank_optimization>C-Rank 알고리즘 최적화</c_rank_optimization>
</naver_specific>
```

---

## 3. 콘텐츠 구조

### 제목 요구사항

```xml
<title_requirements>
    <length min="20" max="35" unit="chars"/>
    <keyword_inclusion mandatory="true"/>
    <click_bait_level>medium</click_bait_level>
    <format>
        <pattern1>{키워드} + 추천/꿀팁/총정리</pattern1>
        <pattern2>{숫자} + {키워드} + 베스트</pattern2>
        <pattern3>{지역} + {키워드} + 후기</pattern3>
    </format>
</title_requirements>
```

### 글 구조

```xml
<content_structure>
    <introduction>
        <length min="3" max="5" unit="lines"/>
        <hook_type>질문형/공감형/충격형/스토리형</hook_type>
        <keyword_placement>첫 2문장 내 필수</keyword_placement>
    </introduction>

    <main_body>
        <subtitles count="5" numbering="required">
            <subtitle_format>숫자. 소제목</subtitle_format>
            <keyword_distribution>각 소제목에 연관 키워드</keyword_distribution>
            <content_per_section min="400" max="500" unit="chars"/>
        </subtitles>
        <paragraph_structure>
            <lines_per_paragraph min="3" max="5"/>
            <chars_per_line min="25" max="30"/>
            <line_break_rules>자연스러운 호흡 단위</line_break_rules>
        </paragraph_structure>
    </main_body>

    <conclusion>
        <length min="2" max="3" unit="sentences"/>
        <cta_type>행동유도/다음글예고/질문/요약</cta_type>
        <keyword_reinforcement>메인 키워드 재강조</keyword_reinforcement>
    </conclusion>
</content_structure>
```

### 길이 제한

```xml
<length_constraints>
    <total_length min="2200" max="2400" unit="chars_no_space"/>
    <distribution>
        <intro_ratio>10%</intro_ratio>
        <body_ratio>80%</body_ratio>
        <conclusion_ratio>10%</conclusion_ratio>
    </distribution>
    <flexibility>±100자 허용</flexibility>
</length_constraints>
```

---

## 4. 톤 & 스타일

### 기본 톤 설정

```xml
<tone_settings>
    <base_tone>
        <formality>casual_polite</formality>
        <emotion_level>medium</emotion_level>
        <emoji_usage>natural</emoji_usage>
        <personality>친근한 이웃</personality>
    </base_tone>
</tone_settings>
```

### 카테고리별 톤

```xml
<category_specific>
    <!-- 애니메이션/영화 -->
    <category name="animation">
        <style>캐주얼한 반말체</style>
        <characteristics>
            - 덕후 문화 용어 사용
            - 밈(meme) 활용 가능
            - 유머러스한 표현
        </characteristics>
        <restrictions>인신공격/비방 금지</restrictions>
    </category>

    <!-- 음식 -->
    <category name="food">
        <style>맛집 탐방 블로거</style>
        <characteristics>
            - 감각적 묘사 (맛, 향, 질감)
            - 개인 경험 강조
            - 디테일한 설명
        </characteristics>
        <vocabulary>쫄깃, 바삭, 고소, 감칠맛</vocabulary>
    </category>

    <!-- 기술/IT -->
    <category name="tech">
        <style>IT 전문 리뷰어</style>
        <characteristics>
            - 전문 용어 + 쉬운 설명
            - 객관적 비교
            - 실용적 팁
        </characteristics>
        <balance>전문성 50% + 대중성 50%</balance>
    </category>

    <!-- 여행 -->
    <category name="travel">
        <style>여행 에세이스트</style>
        <characteristics>
            - 생생한 현장감
            - 감성적 묘사
            - 실용 정보
        </characteristics>
    </category>

    <!-- 패션/뷰티 -->
    <category name="beauty">
        <style>뷰티 인플루언서</style>
        <characteristics>
            - 트렌디한 표현
            - 제품 사용감 상세
            - 비포&애프터
        </characteristics>
    </category>
</category_specific>
```

### 감정 표현

```xml
<emotion_expression>
    <allowed>
        <text_emotions>ㅎㅎ, ㅋㅋ, ㅜㅜ, !!, ~</text_emotions>
        <emoji frequency="moderate">😊 👍 💕 🎉 ✨</emoji>
    </allowed>
    <forbidden>
        <text>ㅅㅂ, ㅈㄴ, 욕설</text>
        <excessive>!!!!!!!, ㅋㅋㅋㅋㅋㅋㅋㅋ</excessive>
    </forbidden>
</emotion_expression>
```

---

## 5. 데이터 소스

### MongoDB 데이터

```xml
<data_sources>
    <mongodb_data>
        <subtitle_pool source="analysis_data" selection="adaptive">
            <pool_size>20-30개</pool_size>
            <selection_strategy>키워드 연관성 우선</selection_strategy>
        </subtitle_pool>

        <expression_library>
            <category>{카테고리}</category>
            <types>
                <opening>도입부 표현</opening>
                <transition>전환 표현</transition>
                <closing>마무리 표현</closing>
                <emphasis>강조 표현</emphasis>
            </types>
        </expression_library>

        <parameter_variables>
            <variable name="size" variation="required">
                <examples>33평→28평, 60L→90L</examples>
            </variable>
            <variable name="price" variation="required">
                <examples>100만원→150만원</examples>
            </variable>
            <variable name="brand" anonymize="true">
                <rule>브랜드명→"반찬" 또는 익명화</rule>
            </variable>
            <variable name="name" variation="required">
                <examples>A씨→F씨</examples>
            </variable>
        </parameter_variables>
    </mongodb_data>
</data_sources>
```

### 템플릿 참조

```xml
<template_reference>
    <source_info>
        <file_name>{파일명}</file_name>
        <template_id>{ID}</template_id>
        <selection_method>{선택 방법}</selection_method>
    </source_info>
    <usage_guidelines>
        <level>inspiration_only</level>
        <modification>필수</modification>
        <persona_differentiation>템플릿과 다른 화자</persona_differentiation>
    </usage_guidelines>
</template_reference>
```

### 참조 원고

```xml
<reference_content>
    <content_type>supplementary</content_type>
    <trust_level>medium</trust_level>
    <usage>
        <extract_facts>사실 정보 추출</extract_facts>
        <ignore_style>스타일 무시</ignore_style>
        <verify_accuracy>정확성 검증 필요</verify_accuracy>
    </usage>
</reference_content>
```

---

## 6. 품질 관리

### 필수 체크리스트

```xml
<quality_criteria>
    <mandatory_checks priority="critical">
        <check id="1">5개 소제목 구조</check>
        <check id="2">2200-2400자 길이</check>
        <check id="3">키워드 자연스러운 배치</check>
        <check id="4">네이버 정책 준수</check>
        <check id="5">모바일 가독성</check>
    </mandatory_checks>

    <optimization_checks priority="high">
        <check>제목 SEO 최적화</check>
        <check>첫 문단 후크 효과</check>
        <check>이미지 위치 힌트</check>
        <check>내부 링크 포인트</check>
        <check>연관 키워드 분산</check>
    </optimization_checks>

    <engagement_checks priority="medium">
        <check>스토리텔링 요소</check>
        <check>개인 경험 진정성</check>
        <check>읽기 흐름 자연스러움</check>
        <check>정보 유용성</check>
    </engagement_checks>
</quality_criteria>
```

### 검증 규칙

```xml
<validation_rules>
    <pre_publish>
        <keyword_density min="3%" max="5%"/>
        <readability_score>초등 6학년 수준</readability_score>
        <duplicate_check>중복률 30% 미만</duplicate_check>
        <grammar_check>맞춤법 검사</grammar_check>
    </pre_publish>

    <post_publish>
        <indexing_check>24시간 내 색인</indexing_check>
        <ranking_monitor>키워드 순위 추적</ranking_monitor>
        <engagement_metrics>체류시간, 스크롤 깊이</engagement_metrics>
    </post_publish>
</validation_rules>
```

---

## 7. 제약사항

### 금지 요소

```xml
<restrictions>
    <forbidden_elements>
        <formatting>
            - 마크다운 문법 (# * - `` [])
            - HTML 태그 (<p> <br> <div>)
            - 특수문자 남용
        </formatting>
        <content>
            - 외부 링크
            - 저작권 침해 콘텐츠
            - 개인정보 노출
            - 광고성 과장 표현
        </content>
    </forbidden_elements>

    <forbidden_patterns>
        <meta_expressions>
            - "요약하자면"
            - "결론적으로"
            - "마무리하자면"
        </meta_expressions>
        <absolute_claims>
            - "최고의"
            - "유일한"
            - "100% 보장"
        </absolute_claims>
        <sensitive_topics>
            - 의료 단정적 조언
            - 법률 자문
            - 투자 보장
        </sensitive_topics>
    </forbidden_patterns>
</restrictions>
```

### 준수 사항

```xml
<compliance>
    <platform_policy>
        <naver>블로그 운영 정책</naver>
        <spam_prevention>저품질 방지</spam_prevention>
    </platform_policy>
    <legal_requirements>
        <kfda>식품/화장품 광고 규정</kfda>
        <kcc>방송통신위원회 가이드라인</kcc>
        <privacy>개인정보보호법</privacy>
    </legal_requirements>
</compliance>
```

---

## 8. 특수 기능

### 페르소나 설정

```xml
<persona_creation>
    <base_persona>
        <demographics>
            <age_group>20-40대</age_group>
            <location>한국</location>
        </demographics>
        <expertise>
            <level>해당 분야 3년차</level>
            <perspective>실사용자 관점</perspective>
        </expertise>
        <voice>
            <tone>친근한 이웃</tone>
            <authenticity>개인 경험 기반</authenticity>
        </voice>
    </base_persona>

    <differentiation>
        <unique_voice>템플릿과 차별화</unique_voice>
        <storytelling>개인 스토리 추가</storytelling>
        <creativity>독창적 관점</creativity>
    </differentiation>
</persona_creation>
```

### 적응형 전략

```xml
<adaptive_strategy>
    <keyword_competition>
        <high_competition>
            <strategy>롱테일 키워드 집중</strategy>
            <content_depth>심화 정보 제공</content_depth>
        </high_competition>
        <low_competition>
            <strategy>메인 키워드 강조</strategy>
            <content_breadth>포괄적 정보</content_breadth>
        </low_competition>
    </keyword_competition>

    <search_intent>
        <informational>정보 제공 중심</informational>
        <commercial>구매 가이드 포함</commercial>
        <navigational>브랜드 정보</navigational>
        <transactional>행동 유도</transactional>
    </search_intent>

    <seasonal_factors>
        <timing>시즌별 트렌드 반영</timing>
        <events>이벤트/행사 연계</events>
    </seasonal_factors>
</adaptive_strategy>
```

### 추가 최적화

```xml
<advanced_optimization>
    <semantic_seo>
        <entity_marking>주요 개체 마킹</entity_marking>
        <topic_clustering>주제 클러스터링</topic_clustering>
    </semantic_seo>

    <user_signals>
        <dwell_time>체류시간 증대 전략</dwell_time>
        <scroll_depth>스크롤 유도</scroll_depth>
        <interaction>댓글/공감 유도</interaction>
    </user_signals>

    <technical_seo>
        <image_optimization>이미지 ALT 텍스트</image_optimization>
        <internal_linking>관련 글 연결</internal_linking>
    </technical_seo>
</advanced_optimization>
```

---

## 9. 통합 구현 예시

### Python 구현 코드

```python
def create_naver_blog_prompt(keyword: str, category: str,
                            mongo_data: dict, ref_content: str,
                            additional_request: str) -> dict:
    """
    네이버 블로그 SEO 최적화 프롬프트 생성
    """

    system_prompt = f"""
<naver_blog_task>
    <self_reflection>
        네이버 블로그 상위노출을 위한 5가지 핵심 체크:
        1. 키워드 최적화 - 자연스러운 배치
        2. 사용자 체류시간 - 흥미로운 구성
        3. 정보 신뢰도 - 정확한 정보
        4. 모바일 가독성 - 적절한 줄바꿈
        5. 네이버 정책 준수 - 스팸 방지
    </self_reflection>

    <seo_optimization>
        <target_platform>naver</target_platform>
        <primary_keyword frequency="high">{keyword}</primary_keyword>
        <keyword_density min="3%" max="5%"/>
    </seo_optimization>

    <content_structure>
        <title_requirements>
            <length min="20" max="35" unit="chars"/>
            <keyword_inclusion mandatory="true"/>
        </title_requirements>
        <main_body>
            <subtitles count="5" numbering="required"/>
        </main_body>
        <length_constraints min="2200" max="2400" unit="chars_no_space"/>
    </content_structure>

    <tone_settings category="{category}">
        {get_category_tone_xml(category)}
    </tone_settings>

    <data_sources>
        <mongodb_data>
            {format_mongodb_data_xml(mongo_data)}
        </mongodb_data>
        <reference_content>
            {ref_content}
        </reference_content>
    </data_sources>

    <quality_criteria priority="ordered">
        <mandatory>키워드 배치, 길이 준수, 5개 소제목</mandatory>
        <optimization>모바일 최적화, 체류시간 증대</optimization>
        <engagement>스토리텔링, 개인 경험</engagement>
    </quality_criteria>

    <restrictions>
        <forbidden>
            - 마크다운/HTML 문법
            - 과장된 광고 표현
            - 메타 표현 (요약하자면 등)
            - 외부 링크
        </forbidden>
    </restrictions>
</naver_blog_task>
"""

    user_prompt = f"""
'{keyword}'에 대한 네이버 블로그 글을 작성해주세요.
카테고리: {category}
추가 요청사항: {additional_request}
"""

    return {
        "system": system_prompt,
        "user": user_prompt,
        "parameters": {
            "model": "gpt-5",
            "reasoning": {"effort": "medium"},
            "verbosity": "high",
            "temperature": 0.7
        }
    }
```

### API 호출 예시

```python
from openai import OpenAI

client = OpenAI()

# 프롬프트 생성
prompt_config = create_naver_blog_prompt(
    keyword="강남 맛집 추천",
    category="food",
    mongo_data=mongodb_data,
    ref_content=reference_text,
    additional_request="20-30대 직장인 타겟"
)

# API 호출 (Responses API)
response = client.responses.create(
    model=prompt_config["parameters"]["model"],
    input=[
        {
            "role": "developer",
            "content": [{
                "type": "input_text",
                "text": prompt_config["system"]
            }]
        },
        {
            "role": "user",
            "content": [{
                "type": "input_text",
                "text": prompt_config["user"]
            }]
        }
    ],
    reasoning=prompt_config["parameters"]["reasoning"],
    verbosity=prompt_config["parameters"]["verbosity"],
    temperature=prompt_config["parameters"]["temperature"]
)

# 결과 출력
print(response.output_text)
```

---

## 📌 사용 가이드

### 1. 태그 선택 가이드

- **필수 태그**: `naver_blog_task`, `seo_optimization`, `content_structure`, `length_constraints`
- **권장 태그**: `quality_criteria`, `tone_settings`, `data_sources`
- **선택 태그**: `persona_creation`, `adaptive_strategy`, `advanced_optimization`

### 2. 카테고리별 커스터마이징

- 각 카테고리의 특성에 맞게 `tone_settings` 조정
- `keyword_strategy`를 업종별 특성에 맞게 수정
- `persona_creation`을 타겟 독자층에 맞게 설정

### 3. 성능 최적화 팁

- XML 태그는 계층적으로 구조화
- 속성(attribute)을 활용하여 구체적인 값 지정
- 우선순위는 `priority` 속성으로 명시
- 검증 가능한 체크리스트 형태로 요구사항 정리

### 4. 주의사항

- 과도한 중첩 방지 (최대 4단계)
- 태그명은 명확하고 직관적으로
- 한글 태그도 가능하나 영문 권장
- GPT-5 특수 기능(`self_reflection`) 활용

---

## 🔄 업데이트 이력

- v1.0 (2024.11): 초기 버전 생성
- 네이버 블로그 정책 변경 시 업데이트 필요
- GPT-5 새로운 기능 추가 시 반영 예정

---

## 📚 참고 자료

- OpenAI GPT-5 Prompting Guide
- OpenAI Cookbook Examples
- Naver Blog SEO Guidelines
- GPT-5 API Documentation
