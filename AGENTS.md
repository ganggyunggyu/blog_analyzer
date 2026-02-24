# PROJECT KNOWLEDGE BASE

**Generated:** 2026-02-24 | **Commit:** ed5475a | **Branch:** main

## OVERVIEW

FastAPI 멀티 AI 엔진(GPT/Claude/Gemini/SOLAR/Grok/DeepSeek/Kimi) 블로그 콘텐츠 생성 플랫폼.
카테고리별 MongoDB 분리 + 45개 전문 프롬프트 + SEO 최적화 후처리 파이프라인.

## STRUCTURE

```
text-gen-hub/
├── api.py                  # FastAPI 진입점 (60+ 라우터 등록, LLM 세마포어)
├── config.py               # .env.{ENV} 로드 → 7개 AI 클라이언트 초기화
├── mongodb_service.py      # MongoDB CRUD + 카테고리별 DB 전환 + 유니크 인덱스
├── cli.py                  # Click CLI (분석, 템플릿, 파라미터, MongoDB 저장)
│
├── routers/                # → routers/AGENTS.md
│   ├── generate/           # 46 AI 원고 생성 엔드포인트
│   ├── bot/                # 12 자동화 라우터 (스케줄, 발행, 큐)
│   ├── search/             # 9 검색/북마크/인기글 라우터
│   ├── analysis/           # 텍스트 분석 (소제목, 업로드)
│   ├── auth/               # 네이버 OAuth + 블로그 자동 발행
│   └── category/, ref/, manuscript/, test/
│
├── llm/                    # → llm/AGENTS.md
│   └── 41 서비스 파일 (엔진별 + 특수목적)
│
├── _prompts/               # → _prompts/AGENTS.md
│   ├── category/           # 45 카테고리 프롬프트 (한국어 파일명)
│   ├── {engine}/           # 엔진별 system/user 프롬프트
│   ├── rules/              # 9 작성규칙 (금지표현, 줄바꿈, 인간체)
│   ├── service/            # MongoDB/참조원고 통합 프롬프트
│   └── common/, viral/, nyangnyang/, ceo/, ...  # 특수목적
│
├── utils/                  # → utils/AGENTS.md
│   ├── ai_client/text.py   # 통합 AI 클라이언트 팩토리 (467줄, 핵심)
│   ├── ai_client/image.py  # 이미지 생성 클라이언트
│   └── text_cleaner, query_parser, format_paragraphs, ...
│
├── analyzer/               # 텍스트 분석 (template, subtitle, expression, morpheme)
├── ai_lib/                 # 줄바꿈 서비스 + 음식 리뷰 파서
├── schema/                 # Pydantic: GenerateRequest, BatchGenerateRequest, ImageGenerateRequest
├── _constants/             # Model.py(39모델), categories.py(66개), text_processing.py
├── _data/                  # 카테고리별 시드 데이터 (23 dirs)
├── _docs/                  # 참조 문서 (114 dirs)
├── services/               # 부가 서비스 로직
├── scripts/                # 유틸 스크립트
└── manuscripts/            # 생성 원고 저장 (completed, failed, pending, queue)
```

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| 새 AI 엔드포인트 추가 | `llm/` → `routers/generate/` → `api.py` | 3파일 수정 |
| 새 카테고리 추가 | `_prompts/category/` → `get_category_tone_rules.py` → `get_category_db_name.py` | 3파일 수정 |
| AI 모델 변경/추가 | `_constants/Model.py` + `config.py` + `utils/ai_client/text.py` | |
| 프롬프트 수정 | `_prompts/{engine}/system.py` or `_prompts/category/*.py` | 기존 카테고리 영향 확인 필수 |
| 줄바꿈/후처리 수정 | `ai_lib/line_break_service.py` + `utils/text_cleaner.py` | |
| MongoDB 스키마 변경 | `mongodb_service.py` | INDEX_MAP 유니크 인덱스 확인 |
| 검색 기능 | `routers/search/` | 9개 엔드포인트 |
| 봇 자동화 | `routers/bot/` | common.py(778줄)가 핵심 공유 로직 |
| 블로그 자동 발행 | `routers/auth/blog_write.py` (539줄) | Playwright 기반 |
| 이미지 생성 | `utils/ai_client/image.py` + `routers/generate/gemini_image.py` | Recraft V3, Imagen 4 |

## REQUEST FLOW

```
POST /generate/{engine}
  ↓ Pydantic 검증 (GenerateRequest)
  ↓ run_in_threadpool()
  ↓ llm/{engine}_service.py
  │  ├─ parse_query(keyword)  → 메인키워드 + 노트 분리
  │  ├─ get_mongo_prompt(category) → MongoDB 데이터 JSON 통합
  │  ├─ get_category_tone_rules(category) → 카테고리 프롬프트
  │  ├─ get_ref_prompt(ref) → 참조원고 스타일 분석
  │  ├─ system = rules + category + mongo + ref 합성
  │  ├─ call_ai(model, system, user) → AI API 호출
  │  └─ 후처리: format_paragraphs → text_clean → line_break
  ↓ MongoDB 저장 (generated 컬렉션)
  ↓ 응답 반환
```

## AI ENGINE MAP

| Engine | Client | Models | Config |
|--------|--------|--------|--------|
| OpenAI | `openai_client` | GPT-5.2, GPT-5-nano, GPT-4o | `config.py:16` |
| Claude | `Anthropic()` | claude-opus-4-5, claude-sonnet-4-5 | `ai_client/text.py` |
| Gemini | `genai.Client()` | gemini-3-pro, gemini-3-flash, gemini-2.5-pro | `ai_client/text.py` |
| SOLAR | `solar_client` (OpenAI compat) | solar-pro, solar-pro2 | `config.py:18` |
| Grok | `grok_client` (xai_sdk) | grok-4-fast-reasoning | `config.py:36` |
| DeepSeek | `deepseek_client` (OpenAI compat) | deepseek-chat, deepseek-reasoner | `config.py` |
| Kimi | `moonshot_client` (OpenAI compat) | kimi-k2.5 | `config.py` |

## CONVENTIONS (THIS PROJECT ONLY)

- **한국어 파일명**: `_prompts/category/` 내 45개 파일이 한국어명 (`위고비.py`, `맛집.py`)
- **패키지 매니저**: `uv` (pip 아님) — `uv sync`, `make dev`, `make install`
- **ENV 기반 .env 로딩**: `ENV=local` → `.env.local`, `ENV=production` → `.env.production`
- **카테고리별 DB 분리**: 카테고리명이 곧 MongoDB 데이터베이스명
- **서비스 함수 네이밍**: `{engine}_gen(user_instructions, ref, category) -> str`
- **라우터 URL**: kebab-case (`/generate/gemini-3-pro`)
- **동시성 제어**: `LLM_CONCURRENCY` 환경변수 → `asyncio.Semaphore`
- **린트/포맷 설정 없음**: 코드 스타일 강제 도구 미사용
- **코멘트/에러 메시지**: 전부 한국어

## ANTI-PATTERNS (CRITICAL)

### 출력 금지 (AI 생성 텍스트)
- 마크다운: `# * - ** __ ~~ []() \`\`\``
- HTML 태그: `<p> <br> <div> <a> <img>`
- URL/도메인: `http:// https:// www. .com`
- 따옴표: `" ' \``
- 특수문자: `· • ◦ ▪ → ※ ★ ☆ ◆ ■`
- 메타 표현: "맺음말", "서론", "도입부"
- 면책문구: "개인차가 있을 수 있습니다", "전문가와 상담하세요"

### AI체 금지 (인간체 필수)
- ❌ "첫째, 둘째, 셋째" / "~해야 합니다" / "요약하자면" / "제공하다"
- ✅ 개인 경험 터치, 대화체, 불완전한 문장, 감정 변화, 시간 표현, 불확실성 표현

### 줄바꿈 (모바일 가독성 - 가장 자주 위반됨)
- 한 줄 30-35자 제한
- 문단 간 반드시 `\n\n` (두 줄 줄바꿈)
- 제목만 줄바꿈 없이

### 코드 금지 패턴
- API 키 하드코딩 금지
- `as any`, `@ts-ignore` 금지
- MongoDB 연결 `finally`에서 `close_connection()` 필수
- 동기 AI 호출을 async 함수에서 직접 실행 금지 → `run_in_threadpool()` 필수
- 빈 catch 블록 금지

## COMMANDS

```bash
# 개발 서버 (자동 리로드)
make dev
# 또는: uv run uvicorn api:app --reload --host 0.0.0.0 --port 8000

# 프로덕션
make start

# 의존성 설치
make install  # = uv sync

# 의존성 업데이트
make update   # = uv lock && uv sync

# CLI 배치 처리
uv run python cli.py

# Docker 로컬
docker-compose up

# 배포 (Fly.io)
fly deploy
```

## NOTES

- **Swagger UI**: `http://localhost:8000/docs` (서버 실행 후)
- **Fly.io 리전**: nrt (도쿄) — 한국 레이턴시 최적화
- **Docker**: Dockerfile(프로덕션, 3.12), Dockerfile.dev(개발, 3.11+Playwright)
- **테스트 프레임워크 없음**: pytest/unittest 미설정, CI/CD 파이프라인 없음
- **대형 파일 주의**: `_prompts/gemini/new_system.py`(1505줄), `llm/blog_filler_pet_service.py`(1015줄), `routers/bot/common.py`(778줄)
- **CLAUDE.md**: 상세 코딩 컨벤션 및 패턴 예시 참조 (이 파일과 중복 최소화)
- **AGENT.md**: 레거시 가이드 (이 AGENTS.md로 대체)