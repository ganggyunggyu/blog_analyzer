# AGENT Guide · blog_analyzer

## 1. Mission Brief
- Automate blog manuscript generation by analyzing legacy posts, storing linguistic assets in MongoDB, and prompting multiple LLM engines (GPT, Claude, Gemini) with enriched context.
- Two touchpoints: `api.py` (FastAPI service) and `main.py` (menu-driven CLI). Both orchestrate the same analyzer/LLM pipeline.
- Repo-root directories of interest: `analyzer/`, `llm/`, `routers/`, `schema/`, `mongodb_service.py`, `_constants/`, `_prompts/`, `_rule/`.

## 2. High-Level Flow
1. **Ingest**: CLI/API pulls `.txt` files from `_data/` or user payloads, then `analyzer/` modules extract morphemes, sentences, expressions, parameters, subtitles, and templates.
2. **Persist**: `mongodb_service.MongoDBService` writes normalized documents into collections (`morphemes`, `sentences`, `expressions`, `parameters`, `templates`, `subtitles`, `manuscripts`). Avoid raw `pymongo` calls outside this service.
3. **Generate**: Service modules in `llm/` compile prompts from `_prompts/` plus DB context, call external LLMs, and stage manuscripts for downstream consumers.

## 3. Backend Architecture
- **Routers (`routers/`)**: Domain-scoped modules (`generate/`, `analysis/`, `category/`, `ref/`). Register new routers in `api.py`. Request/response DTOs belong in `schema/` with Pydantic v2 models.
- **Analyzer (`analyzer/`)**: Keep functions pure and side-effect free. Orchestrators handle I/O while helpers focus on deterministic transformations.
- **LLM Services (`llm/`)**: Wrap OpenAI/Anthropic/Gemini calls. Respect concurrency + model constants from `_constants/`. Never hardcode API keys or model IDs inline.
- **Config & Settings**: `config.py` loads environment; prefer a cached settings accessor for consistency. Add new env keys there (and `.env.example`).
- **Utilities (`utils/`)**: Shared formatters, category mapping, prompt helpers. Centralize reusable logic here before creating ad-hoc helpers elsewhere.

## 4. Python Coding Rules
- Use **absolute imports only** (`from schema.generate import GenerateRequest`).
- Type-hint every function. Introduce `from __future__ import annotations` when forward references arise.
- Data contracts must be `pydantic` models with explicit `Field` metadata and `model_config = {"populate_by_name": True}` when camelCase serialization is required for TS clients.
- Service layer pattern: define interfaces when logic evolves beyond simple pass-throughs, keep DB touchpoints inside dedicated services/repositories.
- Exceptions: extend shared ones (consider adding `src/shared/exceptions.py` if missing) and translate to `HTTPException` in routers.
- Extract magic numbers to `_constants/`. Name them using `UPPER_SNAKE_CASE`.
- Logging: funnel through a shared logger (set up under `src/shared/logging.py` or similar) rather than ad-hoc prints.

## 5. Environment & Tooling
```bash
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
# API (run only if explicitly requested):
uvicorn api:app --reload --port 8000
# CLI (preferred entry for now):
python main.py
```
- `pyproject.toml` currently maps `blog-analyzer = "cli:cli"`; adjust to `main:cli` if you formalize the entry point.
- Required env vars: `OPENAI_API_KEY`, `MONGO_URI`, `MONGO_DB_NAME`, optional `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`, `LLM_CONCURRENCY`.
- Mongo indexes are managed via `MongoDBService.ensure_unique_indexes()`; call once during setup.

## 6. Testing & QA
- Existing smoke suites: `test_api_phase_*.py`, `test_step_by_step.py` at repo root. Extend with `pytest` modules inside `tests/` for unit coverage.
- Mock Mongo or run against a disposable database when writing tests; avoid mutating production collections.
- For orchestrator flows, prefer integration-style tests that seed `_data/` fixtures and assert on resulting collection documents.

## 7. Frontend / TypeScript Handshake
- Consumer apps follow FSD layout (`src/app`, `src/pages`, `src/widgets`, `src/features`, `src/entities`, `src/shared`, `src/assets`).
- Configure absolute imports (e.g., Vite `@/*`, Next.js `baseUrl`). Relative ladders are forbidden.
- Provide a shared `cn` helper combining `clsx` + `tailwind-merge`. Every `className` must route through `cn`.
- Style with Tailwind CSS v4; follow official Next.js/Vite integration guides. Favor icon libraries over emoji for UI polish.
- State management: initialize **Jotai** atoms in `src/shared/state`, but keep actions/mutations inside feature or entity hooks. Do not store actions inside atoms.
- Data fetching: set up **TanStack Query** providers under `src/app/provider`. Wrap entries with `QueryClientProvider` before rendering routes.
- API client contract: expose `createApiClient({ baseUrl, apiKey })` with JSON fetchers. Align TypeScript DTO names (`GenerateRequestDto`, `ManuscriptDoc`) with Python schema fields.
- React components must use `React.Fragment` explicitly (no shorthand) and define props interfaces in PascalCase (`ComponentProps`).

## 8. Cross-Language Data Contracts
| Collection | Python Schema (suggested) | TypeScript Mirror |
| --- | --- | --- |
| `morphemes` | `schema/morpheme.py:MorphemeDoc` | `MorphemeDoc` | 
| `sentences` | `schema/sentence.py:SentenceDoc` | `SentenceDoc` |
| `expressions` | `schema/expression.py:ExpressionDoc` | `ExpressionDoc` |
| `parameters` | `schema/parameter.py:ParameterDoc` | `ParameterDoc` |
| `templates` | `schema/template.py:TemplateDoc` | `TemplateDoc` |
| `subtitles` | `schema/subtitle.py:SubtitleDoc` | `SubtitleDoc` |
| `manuscripts` | `schema/manuscript.py:ManuscriptDoc` | `ManuscriptDoc` |
- Use OpenAPI generation (`pnpm dlx openapi-typescript http://localhost:8000/openapi.json -o src/shared/api/types.ts`) whenever backend contracts shift.

## 9. Operational Guardrails
- Do not start servers unless a task explicitly demands it.
- Keep comments terse and only when essential for non-obvious logic.
- Validate instructions in `_rule/` before introducing new workflows; mirror naming/style expectations there.
- Coordinate commits by concern (analyzer vs service vs router) for clean review diffs.

## 10. Known Gaps & Follow-ups
- Centralize logging and settings modules to align with broader org standards.
- Harden error handling in `llm/` to surface token usage and provider-specific failure reasons.
- Evaluate moving repetitive CLI prompts into reusable components under `run_analyzer/`.
- Consider packaging a TS SDK alongside OpenAPI output for FE teams (align with FSD conventions and TanStack Query usage).

Stay disciplined about Python FSD boundaries and provide TS-first integration points so downstream React/Nest/Vue clients can remain consistent.
