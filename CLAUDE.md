# Blog Analyzer 프로젝트 규칙

## 🎯 프로젝트 개요
이 프로젝트는 **FastAPI 기반의 블로그 원고 분석 및 AI 생성 도구**입니다.
- **주 언어**: Python 3.7+  
- **웹 프레임워크**: FastAPI + Uvicorn
- **데이터베이스**: MongoDB (pymongo)
- **AI 서비스**: OpenAI GPT, Anthropic Claude, Google Gemini, Upstage SOLAR
- **자연어 처리**: KoNLPy, KSS
- **CLI 도구**: Click

## 📁 프로젝트 구조
```
blog_analyzer/
├── main.py                 # CLI 메인 스크립트
├── api.py                  # FastAPI 애플리케이션 진입점
├── config.py               # 환경변수 및 API 클라이언트 설정
├── mongodb_service.py      # MongoDB 연결 및 CRUD 서비스
├── routers/               # FastAPI 라우터들
│   ├── generate/          # AI 원고 생성 라우터들 (gpt, claude, gemini, solar 등)
│   ├── analysis/          # 텍스트 분석 라우터들
│   └── category/          # 카테고리 관련 라우터들
├── llm/                   # LLM 서비스 로직
├── analyzer/              # 텍스트 분석 모듈
├── schema/                # Pydantic 스키마 정의
├── utils/                 # 유틸리티 함수들
├── _prompts/              # AI 프롬프트 템플릿
├── _constants/            # 상수 정의
└── _docs/                 # 문서 관련 파일들
```

## 🎯 코딩 규칙 및 컨벤션

### 1. Python 네이밍 규칙
- **변수, 함수**: snake_case
- **클래스**: PascalCase  
- **상수**: UPPER_SNAKE_CASE
- **파일/모듈**: snake_case
- **비공개 변수/함수**: _leading_underscore

### 2. FastAPI 패턴
```python
# 라우터 정의
from fastapi import APIRouter, HTTPException
from fastapi.concurrency import run_in_threadpool

router = APIRouter()

@router.post("/generate/service")
async def generate_endpoint(request: GenerateRequest):
    # 비동기 처리는 run_in_threadpool 사용
    result = await run_in_threadpool(service_function, params)
    return result
```

### 3. 에러 처리 패턴
```python
try:
    # 메인 로직
    result = some_function()
    return result
except ValueError as e:
    raise HTTPException(status_code=400, detail=str(e))
except Exception as e:
    raise HTTPException(status_code=500, detail=f"내부 오류: {e}")
finally:
    # 리소스 정리 (DB 연결 종료 등)
    if db_service:
        db_service.close_connection()
```

### 4. MongoDB 서비스 패턴
```python
db_service = MongoDBService()
db_service.set_db_name(db_name=category)
try:
    # DB 작업
    db_service.insert_document(collection_name, document)
finally:
    db_service.close_connection()
```

### 5. AI 서비스 호출 패턴
```python
def ai_generate(user_instructions: str, ref: str = "", category: str = "") -> str:
    # API 키 검증
    if not API_KEY:
        raise ValueError("API 키가 설정되어 있지 않습니다.")
    
    # 쿼리 파싱
    parsed = parse_query(user_instructions)
    
    # 프롬프트 생성
    system_prompt = get_system_prompt(category)
    user_prompt = build_user_prompt(parsed, ref)
    
    # AI 호출
    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    )
    
    # 응답 검증 및 후처리
    text = response.choices[0].message.content.strip()
    if not text:
        raise RuntimeError("빈 응답을 받았습니다.")
    
    return comprehensive_text_clean(format_paragraphs(text))
```

### 6. 스키마 정의 패턴
```python
from pydantic import BaseModel
from typing import Optional

class GenerateRequest(BaseModel):
    service: str
    keyword: str  
    ref: str = ""  # 기본값 제공
```

## 🔧 프로젝트별 특수 규칙

### 1. 모듈 Import 순서
```python
# 1. Python 표준 라이브러리
import os
import time
from typing import Optional

# 2. 서드파티 라이브러리  
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

# 3. 프로젝트 내부 모듈
from config import OPENAI_API_KEY
from mongodb_service import MongoDBService
from schema.generate import GenerateRequest
```

### 2. 환경변수 관리
- 모든 API 키는 `.env` 파일에서 관리
- `config.py`에서 중앙집중식 환경변수 로딩
- API 클라이언트도 `config.py`에서 초기화

### 3. 로깅 및 디버깅
```python
print(f"서비스 시작: {service_name}")
print(f"파싱 결과: {parsed}")
print(f"토큰 사용량: in={in_tokens}, out={out_tokens}")
```

### 4. 텍스트 후처리 파이프라인
```python
text = format_paragraphs(text)        # 문단 정리
text = comprehensive_text_clean(text)  # 종합 텍스트 클리닝
```

### 5. MongoDB 문서 구조
```python
document = {
    "content": generated_text,
    "timestamp": time.time(),
    "engine": model_name,
    "service": service_name,
    "category": category,
    "keyword": keyword,
}
```

## 🚀 개발 가이드라인

### 1. 새로운 AI 서비스 추가시
1. `llm/` 폴더에 서비스 모듈 생성
2. `routers/generate/` 에 라우터 추가  
3. `api.py`에 라우터 등록
4. `config.py`에 필요한 클라이언트 추가

### 2. 코드 품질
- 타입 힌트 필수 사용
- Docstring은 필요한 경우에만 간결하게
- 예외 처리는 구체적으로
- 매직넘버 사용 금지

### 3. 테스트 패턴
- API 엔드포인트는 실제 요청으로 테스트
- MongoDB 연결은 테스트 DB 사용
- API 키가 필요한 테스트는 환경변수 체크

## ⚠️ 주의사항
- API 키는 절대 하드코딩 금지
- MongoDB 연결은 반드시 `finally`에서 종료
- 긴 AI 호출은 `run_in_threadpool`로 비동기 처리
- 한국어 텍스트 처리시 인코딩 주의 (`utf-8`)

---

이 규칙들을 따라 일관성 있는 코드를 작성하세요! 🎯