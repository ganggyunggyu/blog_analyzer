# Blog Analyzer - AI 기반 블로그 원고 자동 생성 시스템

**FastAPI 기반의 멀티 AI 엔진 블로그 콘텐츠 생성 플랫폼**

네이버 블로그 바이럴 마케팅을 위한 SEO 최적화 콘텐츠를 AI로 자동 생성하는 서비스입니다.
OpenAI GPT, Anthropic Claude, Google Gemini, Upstage SOLAR, xAI Grok 등 **5가지 AI 엔진**을 지원하며,
**43개 이상의 카테고리별 전문 프롬프트**로 자연스러운 블로그 후기를 생성합니다.

---

## 목차

- [주요 기능](#주요-기능)
- [기술 스택](#기술-스택)
- [프로젝트 구조](#프로젝트-구조)
- [설치 및 실행](#설치-및-실행)
- [API 엔드포인트](#api-엔드포인트)
- [카테고리 시스템](#카테고리-시스템)
- [AI 서비스 비교](#ai-서비스-비교)
- [프롬프트 엔지니어링](#프롬프트-엔지니어링)
- [MongoDB 연동](#mongodb-연동)
- [개발 규칙](#개발-규칙)

---

## 주요 기능

### 핵심 기능

- **멀티 AI 엔진 지원**: GPT-4, GPT-5, Claude Sonnet 4.5, Gemini 2.5, SOLAR, Grok
- **43+ 카테고리 전문화**: 각 카테고리별 맞춤형 프롬프트 엔지니어링
- **SEO 최적화**: 키워드 자연스러운 삽입, 네이버 상위 노출 최적화
- **자연스러운 문체**: AI 티 제거, 실제 사람이 작성한 듯한 구어체
- **참조 원고 학습**: 기존 상위 노출 글 학습 및 스타일 모방
- **MongoDB 데이터 통합**: 카테고리별 DB 데이터 활용
- **텍스트 분석**: 형태소 분석, 문장 구조 분석, 표현 패턴 추출

### 고급 기능

- **단계별 원고 생성**: Phase별 세밀한 원고 제어
- **청크 분할 생성**: 긴 원고를 여러 청크로 나눠 생성
- **배치 처리**: JSONL 포맷 배치 처리 지원
- **실시간 진행률 로깅**: 원고 생성 단계별 실시간 추적

---

## 기술 스택

### Backend Framework
- **FastAPI** - 비동기 웹 프레임워크
- **Uvicorn** - ASGI 서버
- **Python 3.7+**

### AI/ML
- **OpenAI API** (GPT-4 Turbo, GPT-5 Responses API)
- **Anthropic API** (Claude 3.5 Sonnet, Claude Sonnet 4.5)
- **Google Generative AI** (Gemini 2.5 Flash, Gemini 2.0 Flash)
- **Upstage API** (SOLAR LLM)

### NLP
- **KoNLPy** - 한국어 형태소 분석
- **KSS (Korean Sentence Splitter)** - 한국어 문장 분리

### Database
- **MongoDB** (PyMongo) - 카테고리별 데이터 저장
- **MongoDB Atlas** 클라우드 지원

### Infrastructure
- **python-dotenv** - 환경변수 관리
- **CORS Middleware** - API CORS 설정
- **Semaphore** - LLM 동시 호출 제한

---

## 프로젝트 구조

```
blog_analyzer/
├── api.py                      # FastAPI 애플리케이션 진입점
├── config.py                   # 환경변수 및 AI 클라이언트 설정
├── mongodb_service.py          # MongoDB CRUD 서비스
├── cli.py                      # CLI 인터페이스
│
├── routers/                    # FastAPI 라우터
│   ├── generate/               # AI 원고 생성 엔드포인트
│   │   ├── gpt_4_v2.py        # GPT-4 Turbo 생성
│   │   ├── gpt_5_v2.py        # GPT-5 Responses API 생성
│   │   ├── kkk.py             # 멀티 AI 엔진 (GPT/Claude/Gemini)
│   │   ├── claude.py          # Claude 전용
│   │   ├── gemini.py          # Gemini 전용
│   │   ├── solar.py           # SOLAR 전용
│   │   ├── chunk.py           # 청크 분할 생성
│   │   └── step_by_step.py    # 단계별 생성
│   ├── analysis/               # 텍스트 분석 엔드포인트
│   │   ├── get_sub_title.py   # 소제목 추출
│   │   ├── upload_text.py     # 텍스트 업로드 분석
│   │   └── analyzer_router.py # 통합 분석기
│   ├── category/               # 카테고리 관련
│   │   └── keyword.py         # 키워드 추출
│   └── ref/                    # 참조 원고
│       └── get_ref.py         # 참조 원고 조회
│
├── llm/                        # LLM 서비스 로직
│   ├── kkk_service.py         # 멀티 AI 서비스 (핵심)
│   ├── gpt_4_v2_service.py    # GPT-4 서비스
│   ├── gpt_5_v2_service.py    # GPT-5 서비스
│   ├── claude_service.py      # Claude 서비스
│   ├── gemini_service.py      # Gemini 서비스
│   └── chunk_service.py       # 청크 분할 서비스
│
├── _prompts/                   # 프롬프트 엔지니어링
│   ├── category/               # 카테고리별 프롬프트 (32개+)
│   │   ├── 맛집.py
│   │   ├── 미용학원.py
│   │   ├── 공항_장기주차장_주차대행.py
│   │   ├── 위고비.py
│   │   ├── 다이어트.py
│   │   ├── wedding.py
│   │   ├── anime.py
│   │   └── ... (32개 카테고리)
│   ├── service/                # 서비스 프롬프트
│   │   ├── get_mongo_prompt.py   # MongoDB 데이터 통합
│   │   └── get_ref_prompt.py     # 참조 원고 통합
│   └── rules/                  # 작성 규칙
│       ├── anti_ai_writing_patterns.py
│       └── line_break_rules.py
│
├── analyzer/                   # 텍스트 분석 모듈
│   ├── sentence.py            # 문장 분석
│   ├── morpheme.py            # 형태소 분석
│   ├── subtitle.py            # 소제목 분석
│   ├── expression.py          # 표현 패턴 분석
│   └── template.py            # 템플릿 생성
│
├── ai_lib/                     # AI 라이브러리
│   └── line_break_service.py  # 줄바꿈 처리 서비스
│
├── utils/                      # 유틸리티 함수
│   ├── ai_client_factory.py   # AI 클라이언트 팩토리
│   ├── text_cleaner.py        # 텍스트 정제
│   ├── format_paragraphs.py   # 문단 포맷팅
│   ├── query_parser.py        # 쿼리 파싱
│   ├── get_category_db_name.py # 카테고리 DB 매핑
│   └── natural_break_text.py  # 자연스러운 텍스트 분할
│
├── schema/                     # Pydantic 스키마
│   ├── generate.py            # 생성 요청 스키마
│   └── analysis.py            # 분석 요청 스키마
│
└── _constants/                 # 상수 정의
    └── Model.py               # AI 모델 상수
```

---

## 설치 및 실행

### 1. 환경 설정

```bash
# 저장소 클론
git clone <repository-url>
cd blog_analyzer

# 가상환경 생성 (권장)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt
```

### 2. 환경변수 설정

`.env` 파일 생성:

```env
# OpenAI
OPENAI_API_KEY=sk-...

# Anthropic Claude
ANTHROPIC_API_KEY=sk-ant-...

# Google Gemini
GEMINI_API_KEY=...

# Upstage SOLAR
UPSTAGE_API_KEY=...

# xAI Grok
GROK_API_KEY=...

# MongoDB
MONGO_URI=mongodb+srv://...
MONGO_DB_NAME=default_db

# 동시 호출 제한
LLM_CONCURRENCY=3
```

### 3. 서버 실행

```bash
# Uvicorn으로 실행
uvicorn api:app --reload --host 0.0.0.0 --port 8000

# 또는 CLI로 실행
python cli.py
```

서버 실행 후: http://localhost:8000/docs (Swagger UI)

---

## API 엔드포인트

### 원고 생성 (Generate)

#### GPT-4 Turbo
```http
POST /gpt-4-v2/generate
Content-Type: application/json

{
  "service": "헤어미용사_자격증",
  "keyword": "천안미용학원",
  "ref": "참조 원고 텍스트 (선택)"
}
```

#### GPT-5 Responses API
```http
POST /gpt-5-v2/generate
```

#### KKK 멀티 AI (GPT/Claude/Gemini)
```http
POST /kkk/generate
```

- 모델 선택: `llm/kkk_service.py`의 `model_name` 변수로 제어
- 지원 모델:
  - `gpt-4-turbo`
  - `gpt-5o`
  - `claude-sonnet-4-5-20250929`
  - `gemini-2.5-flash-lite`

#### Claude 전용
```http
POST /claude/generate
```

#### Gemini 전용
```http
POST /gemini/generate
```

#### SOLAR 전용
```http
POST /solar/generate
```

### 텍스트 분석 (Analysis)

#### 소제목 추출
```http
POST /analysis/get-sub-title
Content-Type: application/json

{
  "text": "분석할 블로그 원고"
}
```

#### 텍스트 업로드 분석
```http
POST /analysis/upload-text
Content-Type: multipart/form-data

file: 텍스트파일.txt
```

#### 통합 분석
```http
POST /analysis/analyze
```

### 참조 원고 (Reference)

```http
POST /ref/get-ref
Content-Type: application/json

{
  "category": "헤어미용사_자격증"
}
```

---

## 카테고리 시스템

### 지원 카테고리 (43개+)

#### 뷰티/미용
- `미용학원` - 헤어/네일/피부 미용 학원 후기
- `울쎄라` - 피부 리프팅 시술 후기
- `리쥬란` - 피부 재생 시술 후기
- `리들샷` - 피부 개선 시술 후기
- `라미네이트` - 치아 성형 후기
- `beauty_treatment` - 일반 미용 시술

#### 건강/다이어트
- `다이어트` - 일반 다이어트 후기
- `위고비` - 위고비(GLP-1) 다이어트 후기
- `마운자로` - 마운자로 다이어트 주사 후기
- `마운자로_부작용` - 마운자로 부작용 정보
- `서브웨이다이어트` - 서브웨이 다이어트 후기
- `스위치온다이어트` - 스위치온 다이어트 후기
- `브로멜라인` - 브로멜라인 보조제 후기
- `알파CD` - 알파CD 다이어트 보조제
- `에리스리톨` - 제로 칼로리 감미료 후기
- `영양제` - 건강기능식품 후기
- `질분비물` - 여성 건강 정보

#### 여행/생활
- `공항_장기주차장_주차대행` - 인천공항 주차대행 후기
- `맛집` - 맛집 방문 후기
- `wedding` - 결혼 준비/웨딩홀 후기
- `캐리어` - 여행용 캐리어 추천
- `애견동물_반려동물_분양` - 반려동물 분양 정보

#### 교육
- `외국어교육` - 외국어 학습 후기
- `외국어교육_학원` - 외국어 학원 후기

#### 엔터테인먼트
- `anime` - 애니메이션 리뷰
- `movie` - 영화 리뷰

#### 정보/주의
- `텔레그램사기` - 텔레그램 사기 주의 정보
- `틱톡부업사기` - 틱톡 부업 사기 주의 정보
- `족저근막염깔창` - 족저근막염 깔창 추천
- `족저근막염신발_추천` - 족저근막염 신발 추천
- `멜라논크림` - 멜라논 크림 후기

#### 기타
- `기타` - 일반 블로그 포스팅

### 카테고리별 특징

각 카테고리는 독립적인 프롬프트 템플릿을 가지며:

1. **content_essence**: 글의 핵심 정체성
2. **writing_style**: 어조, 문체, 감정 수준
3. **narrative_structure**: 글의 흐름과 단계별 비율
4. **linguistic_patterns**: 자주 쓰는 표현, 전환어
5. **key_components**: 필수/권장/금지 요소
6. **emotional_arc**: 감정 변화 흐름
7. **transformation_examples**: 좋은 예시 vs 나쁜 예시

---

## AI 서비스 비교

| AI 엔진 | 모델명 | 특징 | 추천 용도 |
|---------|--------|------|-----------|
| **GPT-4 Turbo** | `gpt-4-turbo` | 안정적, 높은 품질 | 일반 블로그 원고 |
| **GPT-5** | `gpt-5o` | Responses API, reasoning 지원 | 고급 추론이 필요한 콘텐츠 |
| **Claude Sonnet 4.5** | `claude-sonnet-4-5-20250929` | 자연스러운 문체, 긴 컨텍스트 | 감성적 후기, 긴 원고 |
| **Gemini 2.5 Flash** | `gemini-2.5-flash-lite` | 빠른 속도, 저렴한 비용 | 대량 생성, 빠른 테스트 |
| **Gemini 2.0 Flash** | `gemini-2.0-flash-lite` | 최신 모델, 향상된 성능 | 균형잡힌 품질 |
| **SOLAR** | `solar-pro` | Upstage 한국어 특화 | 한국어 전문 콘텐츠 |
| **Grok** | `grok-4-reasoning` | xAI 추론 모델, 긴 컨텍스트 | 복잡한 추론, 긴 원고 |

### API 파라미터 튜닝

#### GPT-5 / KKK Service
```python
reasoning={"effort": "minimal"}  # minimal, low, medium, high
text={"verbosity": "low"}        # low, medium, high
```

- **effort**: 추론 깊이 (minimal: 빠르고 간결, high: 심도있는 분석)
- **verbosity**: 응답 상세도 (low: 핵심만, high: 풍부한 설명)

---

## 프롬프트 엔지니어링

### 프롬프트 구조

모든 원고는 다음 프롬프트 구조를 따릅니다:

```
[System Prompt]
├── Task Definition (작업 정의)
├── Output Structure (출력 구조)
├── Category Tone Rules (카테고리 규칙)
├── Line Break Rules (줄바꿈 규칙)
├── Human Writing Style (자연스러운 문체)
└── Anti-AI Patterns (AI 티 제거)

[User Prompt]
├── MongoDB Data (카테고리별 DB 데이터)
├── Reference Article (참조 원고)
├── Keyword Integration (키워드 통합)
└── Quality Standards (품질 기준)
```

### 핵심 프롬프트 원칙

#### 1. 금지된 형식 (Forbidden Formats)
```python
# 마크다운 문법
✗ # * - ** __ ~~ []() ```

# HTML 태그
✗ <p> <br> <div> <a> <img>

# 특수문자
✗ · • ◦ ▪ → ※

# 구조 라벨
✗ "서론", "본문", "결론", "들어가며", "마무리"

# 메타 표현
✗ "요약하자면", "결론적으로", "정리하면"

# 어색한 단어
✗ "루틴"
```

#### 2. SEO 최적화
- 키워드 자연스럽게 문맥에 통합
- 제목에 키워드 포함 (20-35자)
- 소제목에 키워드 변형 포함
- 과도한 키워드 반복 금지

#### 3. 자연스러운 문체
- 구어체 존댓말 (반말 금지)
- 감정 표현 풍부하게 (진짜, 정말, 너무)
- 전환어 자연스럽게 사용 (그래서, 그런데, 그렇게)
- 1인칭 경험담 형식

### MongoDB 데이터 통합

카테고리별 MongoDB에 저장된 **상위 노출 글 데이터**를 학습:

```python
# _prompts/service/get_mongo_prompt.py

def get_mongo_prompt(category: str, parsed: dict) -> str:
    """
    MongoDB에서 카테고리별 데이터 조회 후
    프롬프트에 통합하여 스타일 학습
    """
    # 1. MongoDB 연결
    db_service = MongoDBService()
    db_service.set_db_name(db_name=category)

    # 2. 데이터 조회 (상위 5개)
    documents = db_service.find_documents(
        collection_name="articles",
        limit=5
    )

    # 3. 프롬프트 구성
    # - 소제목 리스트
    # - 문체 분석
    # - 키워드 배치 패턴

    return formatted_prompt
```

---

## MongoDB 연동

### 데이터베이스 구조

```
MongoDB Atlas
├── 카테고리1_db (예: 헤어미용사_자격증)
│   ├── articles (상위 노출 글)
│   ├── keywords (키워드 풀)
│   └── analysis (분석 결과)
├── 카테고리2_db (예: 맛집)
│   └── ...
└── generated (생성된 원고)
    ├── content (원고 본문)
    ├── timestamp (생성 시간)
    ├── engine (사용 AI 모델)
    ├── category (카테고리)
    └── keyword (키워드)
```

### MongoDB 서비스 사용

```python
from mongodb_service import MongoDBService

# 초기화
db_service = MongoDBService()

# 카테고리 DB 선택
db_service.set_db_name(db_name="헤어미용사_자격증")

try:
    # 문서 삽입
    db_service.insert_document(
        collection_name="generated",
        document={
            "content": generated_text,
            "timestamp": time.time(),
            "engine": "gpt-4-turbo",
            "category": "헤어미용사_자격증",
            "keyword": "천안미용학원"
        }
    )

    # 문서 조회
    results = db_service.find_documents(
        collection_name="articles",
        query={"keyword": "천안미용학원"},
        limit=5
    )

finally:
    # 반드시 연결 종료
    db_service.close_connection()
```

---

## 개발 규칙

### Python 코딩 컨벤션

```python
# 1. 네이밍 규칙
class GenerateService:           # PascalCase
    API_KEY = "..."             # UPPER_SNAKE_CASE

    def generate_blog(self):     # snake_case
        user_keyword = "..."     # snake_case
        _private_method()        # _leading_underscore

# 2. Import 순서
# Python 표준 라이브러리
import os
import time
from typing import Optional

# 서드파티 라이브러리
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

# 프로젝트 내부 모듈
from config import OPENAI_API_KEY
from mongodb_service import MongoDBService
```

### FastAPI 패턴

```python
from fastapi import APIRouter, HTTPException
from fastapi.concurrency import run_in_threadpool

router = APIRouter()

@router.post("/generate/service")
async def generate_endpoint(request: GenerateRequest):
    """
    비동기 엔드포인트 패턴
    """
    # 동기 함수는 run_in_threadpool로 감싸기
    result = await run_in_threadpool(
        service_function,
        request.keyword,
        request.ref
    )
    return result
```

### 에러 처리 패턴

```python
try:
    # 메인 로직
    result = ai_generate(keyword, ref, category)
    return result

except ValueError as e:
    # 클라이언트 오류 (400)
    raise HTTPException(status_code=400, detail=str(e))

except Exception as e:
    # 서버 오류 (500)
    raise HTTPException(status_code=500, detail=f"내부 오류: {e}")

finally:
    # 리소스 정리
    if db_service:
        db_service.close_connection()
```

### MongoDB 연결 패턴

```python
db_service = MongoDBService()
db_service.set_db_name(db_name=category)

try:
    # DB 작업
    db_service.insert_document(collection_name, document)

finally:
    # 반드시 연결 종료
    db_service.close_connection()
```

---

## 사용 예시

### 1. 미용학원 후기 생성

```bash
curl -X POST "http://localhost:8000/kkk/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "service": "헤어미용사_자격증",
    "keyword": "천안미용학원 헤어미용사 자격증",
    "ref": ""
  }'
```

**생성되는 글 특징:**
- 고등학생/진로 전환자 1인칭 시점
- 진로 고민 → 학원 선택 → 학습 과정 → 합격 흐름
- 처음 가위 잡았을 때의 떨림, 선생님 피드백 등 구체적 에피소드
- 자격증 시험 준비 과정 상세 묘사

### 2. 다이어트 후기 생성 (위고비)

```bash
curl -X POST "http://localhost:8000/gpt-5-v2/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "service": "위고비",
    "keyword": "위고비 다이어트 후기 부작용",
    "ref": ""
  }'
```

**생성되는 글 특징:**
- 위고비 사용 경험 → 부작용 발생 → 대안 발견 구조
- GLP-1 작용 원리 과학적 설명
- 메스꺼움, 비용 부담 등 솔직한 단점
- 유산균/보조제 대안 제시

### 3. 공항 주차대행 후기 생성

```bash
curl -X POST "http://localhost:8000/claude/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "service": "공항_장기주차장_주차대행",
    "keyword": "인천공항 장기주차 주차대행 블루주차대행",
    "ref": ""
  }'
```

**생성되는 글 특징:**
- 여행 준비 → 주차 고민 → 업체 발견 → 이용 경험
- 공식 주차장 vs 사설 업체 가격 비교 (구체적 숫자)
- 발렛 서비스 과정 시간순 묘사
- 안전 장치 (보험, CCTV) 언급

---

## 프로젝트 통계

- **지원 AI 모델**: 6개 (GPT-4, GPT-5, Claude, Gemini, SOLAR, Grok)
- **카테고리 프롬프트**: 43개+
- **API 엔드포인트**: 30개+
- **LLM 서비스**: 30개+
- **코드 라인**: 15,000+ lines
- **평균 원고 길이**: 2,800~3,500자 (공백 제외)
- **생성 시간**: 10~60초 (모델별 상이)

---

## 기여 방법

### 새로운 카테고리 추가

1. `_prompts/category/` 폴더에 프롬프트 파일 생성
```python
# _prompts/category/새카테고리.py

새카테고리 = """
<category_specific_rules category="새카테고리">
  <content_essence>
    글의 핵심 정체성 정의
  </content_essence>

  <writing_style>
    <tone>어조</tone>
    <formality>격식</formality>
    <emotion_level>감정 수준</emotion_level>
  </writing_style>

  <!-- 나머지 구조 정의 -->
</category_specific_rules>
"""
```

2. `llm/kkk_service.py`에 import 추가
```python
from _prompts.category.새카테고리 import 새카테고리
```

3. `utils/get_category_db_name.py`에 매핑 추가
```python
CATEGORY_DB_MAP = {
    "새카테고리": "new_category_db",
    # ...
}
```

4. 테스트 후 커밋

---

## 문제 해결

### 1. MongoDB 연결 오류
```
pymongo.errors.ServerSelectionTimeoutError
```

**해결 방법:**
- `.env` 파일의 `MONGO_URI` 확인
- MongoDB Atlas IP 화이트리스트 확인
- 네트워크 방화벽 확인

### 2. OpenAI API 오류
```
openai.error.RateLimitError
```

**해결 방법:**
- API 키 유효성 확인
- 사용량 한도 확인
- `LLM_CONCURRENCY` 값 줄이기 (기본 3 → 1)

### 3. KoNLPy 설치 오류
```
JPype1 installation error
```

**해결 방법:**
```bash
# macOS
brew install java

# Ubuntu
sudo apt-get install openjdk-11-jdk

# Windows
# JDK 11 수동 설치 필요
```

---

## 라이선스

이 프로젝트는 비공개 프로젝트입니다.

---

## 개발자

**21lab** - AI 블로그 콘텐츠 생성 전문팀

---

## 문의

프로젝트 관련 문의사항은 이슈 트래커를 이용해 주세요.

---

**Made by 21lab**
