# AGENT Guide - blog_analyzer

## Quick Orientation
- FastAPI service plus CLI that generates SEO-oriented manuscripts through multi-engine LLM calls (OpenAI, Claude, Gemini, SOLAR, Grok) and persists aggregates in MongoDB.
- Entry points: `api.py` wires routers under `routers/`; `cli.py` runs the interactive analyzer (keep `main.py` compatibility in mind). Core transformations live in `analyzer/`, prompt orchestration in `llm/`, and persistence in `mongodb_service.py`.
- System assets: `_prompts/` (category prompts, service prompts, writing rules), `_constants/Model.py` (engine registry), `_rule/` (style constraints), `_data/` (seed documents), `output/` (saved manuscripts).

## Bootstrapping
```bash
python -m venv .venv && source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
# API (start only when explicitly approved)
uvicorn api:app --reload --port 8000
# CLI
python main.py  # legacy entry point still supported
```
- Env requirements: `OPENAI_API_KEY`, `MONGO_URI`, `MONGO_DB_NAME`. Optional enhancers: `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`, `UPSTAGE_API_KEY`, `GROK_API_KEY`, `LLM_CONCURRENCY`.
- `MongoDBService.ensure_unique_indexes()` should run once after connection bootstrap to guard against duplicates.

## Backend Architecture
- **Routers (`routers/generate|analysis|category|ref`)**: FastAPI orchestrators; use DTOs from `schema/`, validate input with Pydantic, convert domain errors into `HTTPException`.
- **Analyzer Layer (`analyzer/`)**: pure Python transforms (morpheme -> sentence -> expression -> parameter -> template -> subtitle). Keep functions deterministic; no DB writes or network inside.
- **LLM Services (`llm/`)**: engine-specific clients (e.g., `kkk_service`, `gpt_4_v2_service`, `chunk_service`). Always respect model names from `_constants/Model.py` and persist shared retry/backoff logic here.
- **Config (`config.py`)**: centralizes client wiring and environment parsing. Extend settings here when new providers or knobs appear.
- **Utilities (`utils/`)**: text cleaning, formatting, query parsing, category mapping. Favor these helpers instead of introducing scattered logic.

## Python Delivery Standard (3.8+)
- Use absolute imports (`from src...` style once package is virtualenv-installed) and include `from __future__ import annotations` when forward references appear.
- Every function/class carries explicit type hints; data exchanged with API or CLI must use `pydantic.BaseModel` with `Field` metadata (describe purpose, min/max, regex when relevant).
- Extract constants into `_constants/` (UPPER_SNAKE_CASE). Avoid sprinkling magic numbers/strings inside routers, services, or analyzers.
- Handle side effects through service/repository classes; routers/CLI remain thin controllers.
- Logging goes through a shared logger (extend `logging` utility if necessary); never `print`.

## Frontend Handshake (React / Next.js / Vue)
- Consumers follow FSD folders: `src/app`, `src/pages`, `src/widgets`, `src/features`, `src/entities`, `src/shared`, `src/assets`.
- Absolute imports only (`@/...`) and all `className` composition must pass through a shared `cn` util (`clsx` + `tailwind-merge`).
- Style with Tailwind CSS v4 (follow Next.js or Vite integration guide) and prefer icon libraries over emoji to avoid the "AI wrote this" vibe.
- State baseline:
  - TanStack Query provider configured under `src/app/provider/query-client.tsx`.
  - Global atoms in Jotai under `src/shared/state`; mutations/actions live in hooks (no business logic inside atoms).
  - Domain hooks expose typed handlers that call backend APIs; avoid stuffing actions in stores.
- Generate OpenAPI-driven types for DTO parity:
  ```bash
  pnpm dlx openapi-typescript http://localhost:8000/openapi.json -o src/shared/api/types.ts
  ```

## LLM & Prompt Pipeline
- Category prompts, anti-AI writing rules, and reference templates live in `_prompts/` and `_rule/`. Always reuse these assets instead of duplicating strings.
- When adding an engine, update `_constants/Model.py`, extend `config.py` for the client, and register request/response cleanup in the appropriate `llm/*_service.py`.
- Sanitise outputs through shared cleaners (`utils/format_paragraphs.py`, `utils/text_cleaner.py`) before persistence.
- Respect concurrency controls defined via `LLM_CONCURRENCY` semaphore; long-running tasks should stream progress through structured logging rather than prints.

## Testing & Diagnostics
- Existing smoke scripts (`test_api_phase_*.py`, `test_step_by_step.py`) exercise multi-phase manuscript generation. Expand with `pytest` as needed; keep analyzer tests pure and feed them deterministic fixtures from `_data/`.
- For DB-dependent tests, use isolated collections or mock the `MongoDBService` interface. Never point to production data.
- When verifying new routers, capture OpenAPI snapshots to keep TS clients in sync.

## Workflow Guardrails
- Never start long-running services unless the request explicitly demands it.
- Comments are for essential context only; delete redundant narration.
- Maintain user-authored changes; commit by concern (docs vs backend logic vs prompts).
- Cross-check `_rule/` and `_prompts/` before editing stylistic constraints to avoid breaking downstream SEO tone.

## Persona & Communication
- Responses must blend technical precision with the 케인식 어투 (투박 인천/경기 서부 스타일, 자조 섞인 감정선). Keep profanity masked (`아이고난1`, `나는! 나는..! 장풍을..!! 했다!!`, etc.) and close chaotic tangents with "잠시 소란이 있었어요."
- Avoid emoji in deliverables; rely on text or icon libraries for UI discussions.

Stay disciplined with these rails so Python services, LLM orchestration, and TypeScript consumers move together without slipping on the anti-AI polish requirements.
