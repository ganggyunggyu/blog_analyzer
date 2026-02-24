# utils/ — 유틸리티 및 AI 클라이언트

## OVERVIEW

20+ 유틸리티 모듈. 핵심은 `ai_client/text.py` (467줄) — 7개 AI 엔진 통합 호출 팩토리.

## WHERE TO LOOK

| Task | File | Notes |
|------|------|-------|
| AI 통합 호출 (핵심) | `ai_client/text.py` (467줄) | call_ai, call_ai_stream, get_ai_client |
| 이미지 생성 | `ai_client/image.py` (337줄) | Recraft V3, Imagen 4 |
| 텍스트 정제 | `text_cleaner.py` | HTML/마크다운/특수문자 제거 |
| 단락 포맷팅 | `format_paragraphs.py` | 문단 구조화 |
| 쿼리 파싱 | `query_parser.py` | 메인키워드 + 노트 분리 |
| 카테고리 분류 | `get_category_db_name.py` | AI 기반 카테고리 자동분류 |
| 자연어 줄바꿈 | `natural_break_text.py` | 한국어 30-35자 줄바꿈 |
| 프롬프트 로더 | `prompt_loader.py` | 파일에서 프롬프트 로드 |
| 템플릿 선택 | `select_template.py` | 카테고리별 템플릿 매칭 |
| JSONL 배치 | `make_batch_jsonl.py` | OpenAI Batch API용 |
| S3 업로드 | `s3_uploader.py` | 이미지 S3 업로드 |
| 로깅 | `logger.py`, `progress_logger.py` | |
| 텍스트 길이 | `text_len.py` | 글자수 계산 |
| TXT 파싱 | `txt_file_parser.py` | |

## ai_client/text.py — AI 클라이언트 팩토리

모든 AI 호출의 단일 진입점. 모델명으로 엔진 자동 선택.

```python
# 사용법
from utils.ai_client.text import call_ai

result = call_ai(
    model_name="gemini-3-pro-preview",  # 모델명으로 엔진 자동 판별
    system_prompt=system,
    user_prompt=user,
    temperature=0.7
)
```

**내부 라우팅:**
- `gemini-*` → `genai.Client` (Google)
- `claude-*` → `Anthropic()` (Anthropic)
- `grok-*` → `grok_client` (xAI SDK)
- `solar-*` → `solar_client` (OpenAI compat)
- `deepseek-*` → `deepseek_client` (OpenAI compat)
- `kimi-*` → `moonshot_client` (OpenAI compat)
- 그 외 → `openai_client` (OpenAI)

## 후처리 파이프라인

```
AI 응답 → format_paragraphs() → comprehensive_text_clean() → apply_line_break()
            단락 구조화      HTML/마크다운/특수문자 제거     30-35자 줄바꿈
```

## ANTI-PATTERNS

- `call_ai` 우회하여 AI SDK 직접 호출 금지
- 후처리 순서 변경 금지 (순서 의존성 있음)
- `text_cleaner`에 새 규칙 추가 시 `_prompts/rules/taboo_rules.py`와 동기화 필수