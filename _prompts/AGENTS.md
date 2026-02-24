# _prompts/ — 프롬프트 엔지니어링 시스템

## OVERVIEW

45개 카테고리 프롬프트 + 9개 작성규칙 + 엔진별 system/user 프롬프트 + MongoDB/참조원고 통합 레이어.
AI 호출 전 최종 프롬프트 조립의 핵심 모듈.

## STRUCTURE

```
_prompts/
├── category/               # 45 카테고리별 프롬프트 (한국어 파일명)
│   ├── 맛집.py             # 맛집 리뷰 톤/구조/흐름
│   ├── 위고비.py            # 위고비 후기 전문
│   ├── 애니메이션.py       # 애니 리뷰 (덕후 문체)
│   └── ... (45개 총)
│
├── service/                # 통합 레이어
│   ├── get_mongo_prompt.py # MongoDB 데이터 → JSON 리소스 주입
│   ├── get_ref_prompt.py   # 참조원고 스타일 분석 → JSON
│   └── get_category_tone_rules.py  # 카테고리 → 톤 매핑
│
├── rules/                  # 9 작성규칙 파일
│   ├── taboo_rules.py      # 금지 표현 (마크다운, HTML, URL, 특수문자)
│   ├── human_writing_style.py  # 인간체 6가지 기법
│   ├── line_break_rules.py     # 30-35자/줄, \n\n 강제
│   ├── write_rule.py       # SEO + 5소제목 구조 + 문장다양성
│   └── emphasis/length/output/line_example 규칙
│
├── {engine}/               # 엔진별 system/user 프롬프트
│   ├── gemini/             # new_system.py (1505줄 - 최대 파일)
│   ├── grok/               # 5 프롬프트 파일
│   ├── claude/, gpt/, solar/, deepseek/
│   └── hanryeo/            # system.py (1003줄)
│
├── common/                 # 공통 프롬프트 조각
├── viral/, nyangnyang/, ceo/, kimdongpal/  # 특수목적
├── _private/               # 비공개 프롬프트
├── get_gpt_prompt.py       # GPT 프롬프트 빌더 (734줄)
├── get_gemini_prompt.py    # Gemini 프롬프트 빌더 (568줄)
├── get_kkk_prompts.py      # 멀티AI 통합 프롬프트
├── get_system_prompt.py    # 레거시 시스템 프롬프트 빌더
└── xml.py                  # XML 태그 기반 프롬프트 유틸 (365줄)
```

## PROMPT COMPOSITION PIPELINE

```
요청 (keyword, category, ref)
  ↓
1. get_category_tone_rules(category)
   → _prompts/category/맛집.py 로드
  ↓
2. get_mongo_prompt(category, keyword)
   → MongoDB에서 subtitles/expressions/parameters/templates 추출
   → JSON 리소스 불드
  ↓
3. get_ref_prompt(ref)
   → 참조원고 문장해체 분석 (화자목소리, 리듬, 감정선, 전개, 비율)
   → 스타일 JSON 생성
  ↓
4. 시스템 프롬프트 조립
   system = rules + category_tone + mongo_data + ref_style + conflict_resolution
  ↓
5. call_ai(model, system, user)
```

## CATEGORY TEMPLATE PATTERNS

3가지 패턴 존재:

**구조화형** (맛집): 번호 매긴 흐름 섹션 + 자체 피드백 규칙
```python
맛집 = """
흐름:
1. 친구 추천 방문한 곳
2. 위치와 주차
3. 분위기와 인테리어
4. 내가 먹어본 메뉴들 (압도적으로 길어야 함)
5. 총평 추천
"""
```

**XML기반형** (애니메이션): `<specific><style>...<characteristics>...<constants>` 계층구조

**미니마형** (다이어트): 빈 플레이스홀더, 동적 콘텐츠에 의존

## 카테고리 추가 절차

1. `_prompts/category/새카테고리.py` 생성 (한국어 파일명)
2. `_prompts/service/get_category_tone_rules.py` 의 `TONE_RULES_MAP`에 매핑 추가
3. `utils/get_category_db_name.py`에 DB명 매핑 추가

## CONFLICT RESOLUTION (프롬프트 내 우선순위)

```xml
<conflict_resolution>
  키워드 최적화 vs 자연스러운 문체 → 자연스러움 우선
  목표 글자수 vs 내용 품질 → 품질 우선
  템플릿 참조 vs 독창성 → 독창성 우선
</conflict_resolution>
```

## ANTI-PATTERNS

- 카테고리 프롬프트에 괄호 설명문 포함 → 출력에 그대로 나옴
- 규칙 파일 수정 시 전체 카테고리 영향 미확인
- engine별 프롬프트 변경 시 `get_{engine}_prompt.py` 빌더와 동기화 누락
- `new_system.py` 같은 대형 파일(1505줄) 더 키우지 말 것 — 분리 검토