# llm/ — LLM 서비스 레이어

## OVERVIEW

41개 서비스 파일. 프롬프트 조립 → AI 호출 → 후처리 로직 담당.
모든 서비스는 `{engine}_gen(user_instructions, ref, category) -> str` 인터페이스 준수.

## WHERE TO LOOK

| Task | File | Notes |
|------|------|-------|
| 멀티AI 통합 (핵심) | `kkk_service.py` (334줄) | 모든 엔진 동적 선택 |
| GPT 생성 | `gpt4o_service.py`, `gpt_5_2_service.py` | |
| Claude 생성 | `claude_service.py`, `clean_claude_service.py` | |
| Gemini 생성 | `gemini_3_pro_service.py`, `gemini_3_flash_service.py` | |
| Grok 생성 | `grok_service.py`, `grok_new_service.py` | |
| SOLAR 생성 | `solar_service.py` | |
| DeepSeek 생성 | `deepseek_service.py`, `clean_deepseek_service.py` | |
| 이미지 생성 | `image_service.py` | Recraft V3, Imagen 4 |
| 블로그 필러 | `blog_filler_pet_service.py` (1015줄) | 최대 파일 |
| 댓글 생성 | `comment_service.py`, `recomment_service.py` | |
| 스트리밍 | `stream_service.py` | |
| 배치 | `batch_service.py` | JSONL 기반 |

## SERVICE PATTERN (표준)

```python
from config import openai_client
from utils.query_parser import parse_query
from utils.text_cleaner import comprehensive_text_clean
from _prompts.service.get_mongo_prompt import GPT5MongoPromptBuilder
from _prompts.service.get_category_tone_rules import get_category_tone_rules
from _prompts.service.get_ref_prompt import get_ref_prompt

def {engine}_gen(user_instructions: str, ref: str = "", category: str = "") -> str:
    # 1. 키워드 파싱
    keyword, note = parse_query(user_instructions)
    
    # 2. 프롬프트 조립
    mongo_data = GPT5MongoPromptBuilder(category, keyword).build()
    category_rules = get_category_tone_rules(category)
    ref_prompt = get_ref_prompt(ref) if ref else ""
    system = f"{rules}{category_rules}{mongo_data}{ref_prompt}"
    user = f"'{keyword}'에 대한 네이버 블로그 글을 작성해주세요."
    
    # 3. AI 호출
    result = call_ai(MODEL_NAME, system, user)
    
    # 4. 후처리
    result = comprehensive_text_clean(result)
    result = format_paragraphs(result)
    return result
```

## 새 서비스 추가 절차

1. `llm/new_service.py` 생성 (위 패턴 준수)
2. `routers/generate/new.py` 생성 (라우터 연결)
3. `api.py`에 `include_router` 추가

## CONVENTIONS

- 모델 상수는 `_constants/Model.py`에서 가져올 것
- 동기 AI 호출은 라우터에서 `run_in_threadpool()`로 감싸서 호출
- 후처리 순서: `format_paragraphs` → `comprehensive_text_clean` → `apply_line_break`
- 에러 메시지 한국어로

## ANTI-PATTERNS

- AI 클라이언트 직접 생성 금지 → `config.py` 또는 `utils/ai_client/text.py` 경유
- 프롬프트 하드코딩 금지 → `_prompts/` 모듈에서 import
- 후처리 생략 금지 → 최소 `comprehensive_text_clean` 적용 필수
- `blog_filler_pet_service.py`(1015줄) 패턴 따라가지 말 것 — 분리 필요