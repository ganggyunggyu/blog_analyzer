# Blog Analyzer 프로젝트 규칙

## 프로젝트 개요
이 프로젝트는 **FastAPI 기반의 멀티 AI 엔진 블로그 콘텐츠 생성 플랫폼**입니다.

### 기본 정보
- **주 언어**: Python 3.7+
- **웹 프레임워크**: FastAPI + Uvicorn
- **데이터베이스**: MongoDB (PyMongo) + MongoDB Atlas
- **AI 엔진**: OpenAI GPT, Anthropic Claude, Google Gemini, Upstage SOLAR, xAI Grok (5개)
- **자연어 처리**: KoNLPy, KSS
- **CLI 도구**: Click

### 핵심 기능
- 43개 이상의 카테고리별 전문 프롬프트
- SEO 최적화 블로그 원고 자동 생성
- 참조 원고 학습 및 스타일 모방
- MongoDB 데이터 통합 학습
- 텍스트 분석 및 형태소 분석
- 단계별/청크별 원고 생성

## 프로젝트 구조

```
blog_analyzer/
├── api.py                      # FastAPI 애플리케이션 진입점
├── cli.py                      # CLI 인터페이스
├── config.py                   # 환경변수 및 AI 클라이언트 설정 (GPT, Claude, Gemini, SOLAR, Grok)
├── mongodb_service.py          # MongoDB 연결 및 CRUD 서비스
│
├── routers/                    # FastAPI 라우터 (30개 이상)
│   ├── generate/               # AI 원고 생성 엔드포인트
│   │   ├── gpt_4_v2.py        # GPT-4 Turbo
│   │   ├── gpt_5_v2.py        # GPT-5 Responses API
│   │   ├── claude.py          # Claude Sonnet 4.5
│   │   ├── gemini.py          # Gemini 2.5/2.0 Flash
│   │   ├── grok.py            # Grok AI
│   │   ├── solar.py           # SOLAR LLM
│   │   ├── kkk.py             # 멀티 AI 엔진 (통합)
│   │   ├── chunk.py           # 청크 분할 생성
│   │   ├── step_by_step.py    # 단계별 생성
│   │   └── ... (30개 이상)
│   ├── analysis/               # 텍스트 분석
│   │   ├── analyzer_router.py # 통합 분석기
│   │   ├── get_sub_title.py   # 소제목 추출
│   │   └── upload_text.py     # 텍스트 업로드 분석
│   ├── category/               # 카테고리 관련
│   │   └── keyword.py         # 키워드 추출
│   └── ref/                    # 참조 원고
│       └── get_ref.py         # 참조 원고 조회
│
├── llm/                        # LLM 서비스 로직 (30개 이상)
│   ├── gpt_4_v2_service.py    # GPT-4 서비스
│   ├── gpt_5_v2_service.py    # GPT-5 서비스
│   ├── claude_service.py      # Claude 서비스
│   ├── gemini_service.py      # Gemini 서비스
│   ├── grok_service.py        # Grok 서비스
│   ├── solar_service.py       # SOLAR 서비스
│   ├── kkk_service.py         # 멀티 AI 통합 서비스
│   ├── chunk_service.py       # 청크 분할 서비스
│   ├── step_by/               # 단계별 생성
│   │   ├── step_by_step_service.py
│   │   ├── phase_functions.py
│   │   └── prompts.py
│   └── ... (30개 이상)
│
├── _prompts/                   # 프롬프트 엔지니어링
│   ├── category/               # 카테고리별 프롬프트 (43개)
│   │   ├── 위고비.py
│   │   ├── 마운자로.py
│   │   ├── 다이어트.py
│   │   ├── 미용학원.py
│   │   ├── 공항_장기주차장_주차대행.py
│   │   ├── 울쎄라.py
│   │   ├── 리쥬란.py
│   │   ├── anime.py
│   │   └── ... (43개)
│   ├── service/                # 서비스 프롬프트
│   │   ├── get_mongo_prompt.py   # MongoDB 데이터 통합
│   │   └── get_ref_prompt.py     # 참조 원고 통합
│   └── rules/                  # 작성 규칙
│       ├── anti_ai_writing_patterns.py
│       ├── human_writing_style.py
│       ├── line_break_rules.py
│       └── taboo_rules.py
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
├── _constants/                 # 상수 정의
│   └── Model.py               # AI 모델 상수
│
└── _docs/                      # 문서 및 데이터
```

## 코딩 규칙 및 컨벤션

### Python 네이밍 규칙
- **변수, 함수**: `snake_case`
- **클래스**: `PascalCase`
- **상수**: `UPPER_SNAKE_CASE`
- **파일/모듈**: `snake_case`
- **비공개**: `_leading_underscore`

### FastAPI 라우터 패턴
```python
from fastapi import APIRouter, HTTPException
from fastapi.concurrency import run_in_threadpool
from schema.generate import GenerateRequest

router = APIRouter()

@router.post("/generate/service")
async def generate_endpoint(request: GenerateRequest):
    # 동기 함수는 run_in_threadpool로 감싸기
    result = await run_in_threadpool(
        service_function,
        request.keyword,
        request.ref,
        request.service
    )
    return result
```

### 에러 처리 패턴
```python
try:
    result = ai_generate(keyword, ref, category)
    return result
except ValueError as e:
    raise HTTPException(status_code=400, detail=str(e))
except Exception as e:
    raise HTTPException(status_code=500, detail=f"내부 오류: {e}")
finally:
    if db_service:
        db_service.close_connection()
```

### MongoDB 연결 패턴
```python
db_service = MongoDBService()
db_service.set_db_name(db_name=category)
try:
    db_service.insert_document(collection_name, document)
finally:
    db_service.close_connection()  # 반드시 연결 종료
```

### AI 서비스 호출 패턴
```python
def ai_generate(user_instructions: str, ref: str = "", category: str = "") -> str:
    # 1. API 키 검증
    if not API_KEY:
        raise ValueError("API 키가 설정되어 있지 않습니다.")

    # 2. 쿼리 파싱
    parsed = parse_query(user_instructions)

    # 3. 프롬프트 생성 (카테고리별, MongoDB 데이터, 참조 원고 통합)
    system_prompt = get_system_prompt(category)
    user_prompt = build_user_prompt(parsed, ref, category)

    # 4. AI 호출
    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    )

    # 5. 후처리 (줄바꿈, 텍스트 정제)
    text = response.choices[0].message.content.strip()
    if not text:
        raise RuntimeError("빈 응답을 받았습니다.")

    text = format_paragraphs(text)
    text = comprehensive_text_clean(text)
    text = apply_line_break(text)  # ai_lib의 줄바꿈 서비스

    return text
```

### Pydantic 스키마 패턴
```python
from pydantic import BaseModel

class GenerateRequest(BaseModel):
    service: str      # 카테고리명
    keyword: str      # 키워드
    ref: str = ""     # 참조 원고 (선택)
```

## 프로젝트 특수 규칙

### Import 순서
```python
# 1. Python 표준 라이브러리
import os
import time
from typing import Optional

# 2. 서드파티 라이브러리
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

# 3. 프로젝트 내부 모듈
from config import OPENAI_API_KEY, grok_client
from mongodb_service import MongoDBService
from schema.generate import GenerateRequest
from utils.ai_client_factory import call_ai
from ai_lib.line_break_service import apply_line_break
```

### 환경변수 관리
**`.env` 파일 구성:**
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
```

**`config.py`에서 초기화:**
```python
from dotenv import load_dotenv
from openai import OpenAI
from xai_sdk import Client

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GROK_API_KEY = os.getenv("GROK_API_KEY")

openai_client = OpenAI(api_key=OPENAI_API_KEY)
grok_client = Client(api_key=GROK_API_KEY, timeout=3600)
solar_client = OpenAI(
    api_key=UPSTAGE_API_KEY,
    base_url="https://api.upstage.ai/v1/solar"
)
```

### 텍스트 후처리 파이프라인
```python
# 1. 문단 포맷팅
text = format_paragraphs(text)

# 2. 텍스트 클리닝 (특수문자, HTML, 마크다운 제거)
text = comprehensive_text_clean(text)

# 3. 줄바꿈 규칙 적용 (AI 라이브러리)
text = apply_line_break(text, model_name=Model.GPT5)
```

### MongoDB 문서 구조
```python
document = {
    "content": generated_text,
    "timestamp": time.time(),
    "engine": model_name,       # "gpt-4-turbo", "claude-sonnet-4-5", "grok-4"
    "service": service_name,    # 카테고리명
    "category": category,       # DB 이름
    "keyword": keyword,
}
```

### 로깅 및 디버깅
```python
print(f"서비스: {service_name}")
print(f"키워드: {keyword}")
print(f"원고 길이: {len(text)} (공백 제외: {len(text.replace(' ', ''))})")
print(f"토큰: in={in_tokens}, out={out_tokens}")
```

## 개발 가이드라인

### 새로운 AI 서비스 추가 방법
1. **`config.py`에 클라이언트 추가**
   ```python
   NEW_API_KEY = os.getenv("NEW_API_KEY")
   new_client = NewClient(api_key=NEW_API_KEY)
   ```

2. **`llm/new_service.py` 생성**
   ```python
   from config import new_client
   from _prompts.category import 위고비, 다이어트

   def new_gen(user_instructions: str, ref: str = "", category: str = "") -> str:
       # 구현
   ```

3. **`routers/generate/new.py` 생성**
   ```python
   from llm.new_service import new_gen

   @router.post("/new/generate")
   async def generate(request: GenerateRequest):
       return await run_in_threadpool(new_gen, ...)
   ```

4. **`api.py`에 라우터 등록**
   ```python
   from routers.generate.new import router as new_router
   app.include_router(new_router)
   ```

### 새로운 카테고리 추가 방법
1. **`_prompts/category/새카테고리.py` 생성**
   ```python
   새카테고리 = """
   ## 메인 키워드:
   새카테고리

   ## 서브 키워드:
   - 관련키워드1
   - 관련키워드2

   ## 금지사항
   - 금지할 내용

   ## 필수사항
   - 반드시 포함할 내용

   ## 화자
   - 페르소나 설명
   """
   ```

2. **해당 서비스 파일에 import**
   ```python
   # llm/grok_service.py 등
   from _prompts.category import 새카테고리
   ```

3. **`get_category_tone_rules()` 함수에 추가**
   ```python
   tone_rules_map = {
       "새카테고리": 새카테고리.새카테고리,
       # ...
   }
   ```

4. **`utils/get_category_db_name.py`에 매핑 추가**
   ```python
   CATEGORIES = [
       "새카테고리",
       # ...
   ]
   ```

### 코드 품질 규칙
- **타입 힌트 필수**: `def func(text: str) -> str:`
- **Docstring 최소화**: 중요한 것만 간결하게
- **예외 처리 구체적으로**: `ValueError`, `HTTPException` 등
- **매직넘버 금지**: 상수로 정의

### 테스트 방법
- **API 엔드포인트**: 실제 HTTP 요청으로 테스트
- **MongoDB 연결**: 테스트 DB 사용
- **API 키**: 환경변수 체크 후 테스트

## 주의사항
- API 키는 절대 하드코딩 금지
- MongoDB 연결은 반드시 `finally`에서 종료
- 긴 AI 호출은 `run_in_threadpool`로 비동기 처리
- 한국어 텍스트는 `utf-8` 인코딩
- 프롬프트 수정 시 기존 카테고리 영향 확인

## 주요 유틸리티
- **`utils/ai_client_factory.py`**: AI 클라이언트 통합 호출
- **`utils/text_cleaner.py`**: 텍스트 정제 (HTML, 마크다운, 특수문자 제거)
- **`utils/query_parser.py`**: 키워드 쿼리 파싱
- **`ai_lib/line_break_service.py`**: 줄바꿈 규칙 적용

---

이 규칙을 따라 일관성 있는 코드를 작성하세요.