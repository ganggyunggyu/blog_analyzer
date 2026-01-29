# Text Gen Hub - 개발 가이드

## 프로젝트 개요
- **타입**: FastAPI + Python 멀티 AI 엔진 블로그 콘텐츠 생성 플랫폼
- **패키지 매니저**: uv (pyproject.toml)
- **Python 버전**: 3.11+
- **데이터베이스**: MongoDB (PyMongo) + MongoDB Atlas
- **배포**: Fly.io (Docker)

## AI 엔진 (6개)
| 엔진 | 클라이언트 | 모델 예시 |
|------|-----------|----------|
| OpenAI GPT | `openai_client` | gpt-4o, gpt-4-turbo |
| Anthropic Claude | anthropic SDK | claude-sonnet-4-5 |
| Google Gemini | google-genai | gemini-2.5-flash |
| Upstage SOLAR | `solar_client` | solar-pro |
| xAI Grok | `grok_client` | grok-4 |
| DeepSeek | `deepseek_client` | deepseek-chat |

## 디렉토리 구조
```
text-gen-hub/
├── api.py                 # FastAPI 진입점
├── cli.py                 # CLI 인터페이스
├── config.py              # 환경변수 및 AI 클라이언트
├── mongodb_service.py     # MongoDB CRUD
│
├── routers/               # FastAPI 라우터
│   ├── generate/          # 원고 생성 (25개)
│   │   ├── gpt4o.py, chatgpt4o.py
│   │   ├── claude.py, clean_claude.py
│   │   ├── gemini_3_flash.py, gemini_3_pro.py
│   │   ├── grok.py, grok_new.py
│   │   ├── solar.py, deepseek.py
│   │   └── kkk.py (멀티 AI 통합)
│   ├── analysis/          # 텍스트 분석
│   ├── category/          # 카테고리 관리
│   ├── ref/               # 참조 원고
│   ├── search/            # 검색 (9개)
│   └── manuscript/        # 원고 관리
│
├── llm/                   # LLM 서비스 로직 (25개)
│   ├── gpt4o_service.py
│   ├── claude_service.py
│   ├── gemini_3_flash_service.py
│   ├── grok_service.py
│   ├── deepseek_service.py
│   └── kkk_service.py
│
├── _prompts/              # 프롬프트 엔지니어링
│   ├── category/          # 카테고리별 프롬프트 (45개+)
│   ├── gpt/, gpt4o/       # GPT 전용 프롬프트
│   ├── claude/            # Claude 전용 프롬프트
│   ├── gemini/            # Gemini 전용 프롬프트
│   ├── grok/              # Grok 전용 프롬프트
│   ├── deepseek/          # DeepSeek 전용 프롬프트
│   ├── solar/             # SOLAR 전용 프롬프트
│   ├── rules/             # 작성 규칙
│   ├── service/           # 서비스 프롬프트
│   └── common/            # 공통 프롬프트
│
├── analyzer/              # 텍스트 분석 모듈
├── ai_lib/                # AI 라이브러리 (줄바꿈 등)
├── utils/                 # 유틸리티 (18개)
├── schema/                # Pydantic 스키마
├── _constants/            # 상수 정의
├── _docs/                 # 학습용 문서
└── _data/                 # 시드 데이터
```

## 실행 명령어
```bash
# 가상환경 설정 (uv)
uv sync
source .venv/bin/activate

# 개발 서버
uvicorn api:app --reload --port 8000

# 또는 run 스크립트
./run

# CLI
python cli.py
```

## 환경변수 (.env)
```env
# AI API Keys
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GEMINI_API_KEY=...
UPSTAGE_API_KEY=...
GROK_API_KEY=...
DEEPSEEK_API_KEY=...

# MongoDB
MONGO_URI=mongodb+srv://...
MONGO_DB_NAME=default_db

# AWS S3
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_S3_BUCKET=...

# 동시성
LLM_CONCURRENCY=3
```

## 개발 규칙

### 라우터 패턴
```python
from fastapi import APIRouter
from fastapi.concurrency import run_in_threadpool
from schema.generate import GenerateRequest

router = APIRouter()

@router.post("/generate/service-name")
async def generate(request: GenerateRequest):
    result = await run_in_threadpool(
        service_function,
        request.keyword,
        request.ref,
        request.service
    )
    return result
```

### LLM 서비스 패턴
```python
from config import openai_client
from _prompts.category import 카테고리명

def generate(user_instructions: str, ref: str = "", category: str = "") -> str:
    # 1. 프롬프트 생성
    # 2. AI 호출
    # 3. 후처리 (텍스트 정제, 줄바꿈)
    return text
```

### 새 엔드포인트 추가
1. `llm/new_service.py` 생성
2. `routers/generate/new.py` 생성
3. `api.py`에 라우터 등록

### 새 카테고리 추가
1. `_prompts/category/새카테고리.py` 생성
2. 해당 서비스 파일에 import
3. `utils/get_category_db_name.py` 매핑 추가

## 주요 카테고리 (45개+)
위고비, 마운자로, 다이어트, 미용학원, 울쎄라, 리쥬란,
공항_장기주차장, 애니메이션, 맛집, 호텔, 웨딩홀,
블록체인_가상화폐, 커피머신, 영화리뷰, 노래리뷰 등

## 주의사항
- API 키 하드코딩 금지
- MongoDB 연결은 `finally`에서 종료
- 긴 AI 호출은 `run_in_threadpool`로 비동기 처리
- 프롬프트 수정 시 기존 카테고리 영향 확인
- 서버 실행은 명시적 요청 시에만

## 케인식 어투
대화형 응답에서 케인 캐릭터 말투 사용:
- "아이고난1", "오옹! 나이스!"
- "잠시 소란이 있었어요"
- 개발 문서/코드는 전문적 어조 유지
