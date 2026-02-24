# routers/ — API 라우터 계층

## OVERVIEW

83개 라우터 파일, 7개 도메인 서브디렉토리. 모든 비즈니스 로직은 `llm/` 또는 전담 모듈로 위임.

## STRUCTURE

```
routers/
├── generate/       # 46파일 — AI 원고 생성 (80% 트래픽)
├── bot/            # 12파일 — 자동화/스케줄/발행/큐
├── search/         # 9파일 — 검색/북마크/인기글/통계
├── analysis/       # 4파일 — 텍스트 분석 (소제목, 업로드)
├── auth/           # 3파일 — 네이버 OAuth + 블로그 자동발행
├── category/       # 키워드 추출
├── ref/            # 참조원고 조회
├── manuscript/     # 원고 관리 (visibility)
└── test/           # 헬스체크
```

## ENDPOINT URL 규칙

- kebab-case: `/generate/gemini-3-pro`, `/generate/gpt-ver3-clean`
- 도메인 접두사: `/generate/`, `/search/`, `/analysis/`, `/auth/`, `/bot/`
- 테스트: `/generate/test-*` 네임스페이스

## generate/ 도메인 (46파일)

**엔진별 라우터:**
| 엔진 | 라우터 | 서비스 |
|--------|----------|----------|
| GPT | gpt4o, chatgpt4o, gpt_5_2, gpt_ver3_clean, gpt_ceo | llm/gpt*_service |
| Claude | claude, clean_claude | llm/claude_service |
| Gemini | gemini_3_pro, gemini_3_flash, gemini_new, gemini_cafe, gemini_ceo, gemini_image | llm/gemini*_service |
| Grok | grok, grok_new, grok_ver3_clean, grok_hanryeo | llm/grok*_service |
| SOLAR | solar, solar_ver3_clean | llm/solar_service |
| DeepSeek | deepseek, deepseek_new, clean_deepseek | llm/deepseek*_service |
| 멀티AI | kkk (/generate/test) | llm/kkk_service |

**특수목적:** nyangnyang, kimdongpal, hanryeo, ghost_story, keyword_generator
**배치/스트림:** generate_batch, generate_stream
**댓글:** generate_comment, generate_recomment

## ROUTER PATTERN (표준)

```python
from fastapi import APIRouter
from fastapi.concurrency import run_in_threadpool
from schema.generate import GenerateRequest
from mongodb_service import MongoDBService

router = APIRouter()

@router.post("/generate/{service-name}")
async def generate(request: GenerateRequest):
    db = MongoDBService()
    db.set_db_name(request.service)
    try:
        result = await run_in_threadpool(
            service_gen, request.keyword, request.ref, request.service
        )
        db.insert_document("generated", {"content": result, ...})
        return {"result": result}
    finally:
        db.close_connection()
```

## bot/ 도메인 (12파일)

- `common.py` (778줄): 핵심 공유 로직 — 스케줄링, 발행, 큐 관리
- `auto_schedule.py` (407줄): 자동 스케줄 실행
- `router.py`: 통합 라우터 등록

## auth/ 도메인

- `naver.py`: 네이버 OAuth 인증
- `blog_write.py` (539줄): Playwright 기반 블로그 자동 발행

## ANTI-PATTERNS

- 라우터에 비즈니스 로직 직접 작성 금지 → `llm/` 위임
- `run_in_threadpool` 누락 금지 → 동기 AI 호출 직접 await 불가
- MongoDB 연결 `finally` 누락 금지
- clean/new 버전 라우터 남발 주의 — 통합 검토 필요