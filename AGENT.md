# AGENT Guide · blog_analyzer

## 1. Snapshot
- Python FastAPI + CLI that ingests manuscripts into MongoDB, enriches prompts, and hits multi-engine LLM services (OpenAI, Claude, Gemini, SOLAR, Grok).
- Entry points: `api.py` (FastAPI routers under `routers/`), `main.py` (CLI workflow). Shared business logic lives in `analyzer/`, `llm/`, `mongodb_service.py`.
- Prompt assets: `_prompts/`, `_constants/Model.py`, `_rule/`. Data seeds under `_data/`, outputs saved to `output/`.

## 2. Runbook
```bash
python -m venv .venv && source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
# API (only on explicit request)
uvicorn api:app --reload --port 8000
# CLI (interactive menu)
python main.py
```
- Required env: `OPENAI_API_KEY`, `GROK_API_KEY`, `MONGO_URI`, `MONGO_DB_NAME`. Optional: `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`, `UPSTAGE_API_KEY`, `LLM_CONCURRENCY`.
- Mongo indexes via `MongoDBService.ensure_unique_indexes()`; call during init once.

## 3. Architecture Notes
- **Routers (`routers/generate|analysis|ref|category`)**: expose FastAPI endpoints. DTOs live in `schema/`. Wrap errors with `HTTPException`.
- **Analyzer (`analyzer/`)**: pure data transforms (morphemes → sentences → expressions → parameters → templates → subtitles). No DB writes here.
- **LLM Layer (`llm/`)**: orchestrators per engine. `kkk_service` routes to OpenAI/SOLAR/Gemini/Claude/Grok using prompts from `_prompts/`. Respect model names from `_constants/Model.py`.
- **Config (`config.py`)**: centralizes clients (`openai_client`, `solar_client`, `grok_client`, etc.). Add env keys + dependency wiring here.
- **Utils**: formatting, parsing, cleaning helpers. Prefer existing utils before introducing new ones.

## 4. Coding Standards (Python 3.8+)
- Absolute imports only; enable `from __future__ import annotations` when forward refs show up.
- Type-hint every function, use Pydantic models (`schema/`) with `Field` metadata and `model_config = {"populate_by_name": True}` if camelCase serialization is needed.
- Extract magic numbers to `_constants/` (UPPER_SNAKE_CASE).
- Services mediate DB side effects; keep CLI/API layers thin.
- Logging: prefer centralized logger (extend `logging` util instead of `print`).

## 5. Frontend Handshake (React / Next / Vue)
- Consumers follow FSD layout (`src/app`, `src/pages`, `src/widgets`, `src/features`, `src/entities`, `src/shared`, `src/assets`).
- Absolute imports only (`@/shared`, `@/entities`).
- Provide shared `cn` helper (`clsx` + `tailwind-merge`); every `className` must pass through `cn`.
- Styling via Tailwind v4 per official Next/Vite guides; prefer icon libs over emoji.
- State: initialize Jotai atoms under `src/shared/state`; actions/mutations live in hooks (no action storage inside atoms).
- Queries: register TanStack Query provider under `src/app/provider/query-client.tsx`. Mutations/fetchers consume backend via typed DTOs.
- OpenAPI → TS types: `pnpm dlx openapi-typescript http://localhost:8000/openapi.json -o src/shared/api/types.ts`.

## 6. LLM Service Checklist
- Honor `Model` enum; update `_constants/Model.py` when introducing engines.
- Use shared prompts from `_prompts/` (system + user). Keep `anti_ai_writing_patterns` and `human_writing_style` enforced.
- When branching for a new provider (e.g., Grok), wire the client in `config.py`, guard missing API keys, and normalize response text before cleaning via `comprehensive_text_clean`.
- Token/length sanity: print (or better, log) `len` diagnostics, never expose secrets.

## 7. Testing
- Smoke scripts at repo root (`test_api_phase_*.py`, `test_step_by_step.py`). Extend with `pytest` as needed.
- Mock or sandbox Mongo for unit tests; avoid production data mutation.
- Prefer deterministic fixtures in `_data/` for analyzer tests.

## 8. Workflow Guardrails
- Do not start servers unless requested. Keep comments minimal + purposeful.
- Commit by concern (docs vs services). Never revert user-authored changes.
- Validate `_rule/` instructions before altering prompts or templates.

Stay aligned with these guardrails to keep Python services and TypeScript consumers in sync.
