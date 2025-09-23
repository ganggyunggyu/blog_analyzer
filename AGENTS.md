# AGENTS Guide (Tailored for blog_analyzer)

This repo is a Python FastAPI service + CLI for blog manuscript analysis and generation backed by MongoDB and OpenAI. Our consumer apps are TypeScript-first (React/NestJS/Vue), so this guide bridges Python internals with TypeScript client conventions and testing.

## Architecture Overview
- API: `FastAPI` app in `api.py`, routers under `routers/` (e.g., `/generate/gpt`, `/manuscript/ingest`, `/analysis/...`).
- CLI: menu-style `click` tool in `main.py` to analyze local `.txt` files and persist results to MongoDB.
- LLM: OpenAI (and others) under `llm/`, primary entry is `llm/gpt_4_service.py` using `MongoDBService` aggregates.
- DB: `mongodb_service.py` with collections: `morphemes`, `sentences`, `expressions`, `parameters`, `templates`, `subtitles`, `manuscripts`.
- Analysis pipeline: `analyzer/` modules for morphemes/sentences/expressions/parameters/templates/subtitles.

Known caveats
- `pyproject.toml` declares `blog-analyzer = "cli:cli"` but no `cli.py`. Use `python main.py` for now (or fix to `main:cli`).
- Some magic numbers exist (e.g., `MAX_TEXT_LEN` in `routers/ingest.py`, API delays in `main.py`). See “Constants & Naming”.

## Environment & Run
- Python: `>=3.10` recommended (fastapi/pydantic v2).
- Setup
  - `python -m venv .venv && source .venv/bin/activate`
  - `pip install -r requirements.txt`
- Env vars (`.env`)
  - `OPENAI_API_KEY`, `ANTHROPIC_API_KEY` (optional), `GEMINI_API_KEY` (optional)
  - `MONGO_URI`, `MONGO_DB_NAME`
  - `LLM_CONCURRENCY` (default 3)
- Run API
  - `uvicorn api:app --reload --port 8000`
  - Swagger: `http://localhost:8000/docs`, OpenAPI JSON: `/openapi.json`
- Run CLI (interactive menu)
  - `python main.py`

## Project Structure (Python)
- Root scripts/config (.env, `api.py`, `main.py`, `config.py`)
- `analyzer/`: text analysis steps (pure functions; side-effects at orchestration level only)
- `llm/`: prompt + model calls (OpenAI, etc.)
- `routers/`: FastAPI modular routers grouped by domain (`generate/`, `analysis/`, `category/`, `ref/`)
- `schema/`: `pydantic` request/response models
- `utils/`: helpers (category parsing, formatting, etc.)
- `_prompts/`, `_constants/`, `_docs/`, `_data/`: supporting assets

## Conventions (Bridge to TS rules)
When we modify Python, mirror TS naming and clarity:
- Naming
  - variables/functions: `snake_case` in Python, but boolean must be explicit in meaning; prefer `is_...`, `has_...`.
  - constants: `UPPER_SNAKE_CASE` (e.g., `MAX_TEXT_LEN`, `API_DELAY_EXPR`). Extract magic numbers to constants.
  - CRUD prefixes in service methods: `create/get/update/remove_*`.
- DTOs
  - Define request/response models in `schema/` with `pydantic` v2, annotate fields, and short `description`.
  - Keep keys stable and compatible with TS clients (lowerCamelCase in JSON via `model_config = {"populate_by_name": True}` and `Field(serialization_alias="lowerCamel")` when needed).
- API
  - One router per domain, add to `api.py` via `app.include_router(...)`.
  - Document summary/description on endpoints; FastAPI auto-generates Swagger.
- Side effects
  - DB writes via `MongoDBService` only; do not write from analyzer functions.
- Errors
  - Use `HTTPException` in routers; in CLI raise `click.ClickException` for invalid input.

## TypeScript Client Guide
Use OpenAPI to generate types, then write small clients/hooks.

- Generate types (local dev)
  - `pnpm dlx openapi-typescript http://localhost:8000/openapi.json -o src/shared/api/types.ts`

- Minimal fetch client (`src/shared/api/client.ts`)
  ```ts
  export interface ApiClientConfig { baseUrl: string; apiKey?: string }

  export const createApiClient = (config: ApiClientConfig) => {
    const { baseUrl, apiKey } = config

    const getHeaders = (): HeadersInit => ({
      'Content-Type': 'application/json',
      ...(apiKey ? { Authorization: `Bearer ${apiKey}` } : {}),
    })

    const post = async <TReq, TRes>(path: string, body: TReq): Promise<TRes> => {
      const res = await fetch(`${baseUrl}${path}`, {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify(body),
      })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      return (await res.json()) as TRes
    }

    return { post }
  }
  ```

- DTOs (TS, aligned with Python)
  ```ts
  export interface GenerateRequestDto {
    service: 'gpt' | 'claude' | 'solar'
    keyword: string
    ref: string
  }

  export interface ManuscriptDoc {
    _id?: string
    content: string
    timestamp: number
    engine: string
    keyword: string
  }
  ```

- Feature example: call `/generate/gpt` (React)
  ```ts
  import React from 'react'

  export interface UseGenerateGptParams { baseUrl: string }
  export interface UseGenerateGptState {
    isLoading: boolean
    error?: string
    manuscript?: ManuscriptDoc
  }

  export const useGenerateGpt = ({ baseUrl }: UseGenerateGptParams) => {
    const [state, setState] = React.useState<UseGenerateGptState>({ isLoading: false })

    const handleGenerate = React.useCallback(async (payload: GenerateRequestDto) => {
      setState(s => ({ ...s, isLoading: true, error: undefined }))
      try {
        const res = await fetch(`${baseUrl}/generate/gpt`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        })
        if (!res.ok) throw new Error(`HTTP ${res.status}`)
        const manuscript = (await res.json()) as ManuscriptDoc
        setState({ isLoading: false, manuscript })
        return manuscript
      } catch (e: unknown) {
        setState({ isLoading: false, error: (e as Error).message })
        throw e
      }
    }, [baseUrl])

    return { ...state, handleGenerate }
  }
  ```

- NestJS-style service for SSR/Backend
  ```ts
  import { Injectable } from '@nestjs/common'

  @Injectable()
  export class ManuscriptService {
    constructor(private readonly baseUrl: string) {}

    async createGptManuscript(payload: GenerateRequestDto): Promise<ManuscriptDoc> {
      const res = await fetch(`${this.baseUrl}/generate/gpt`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      return (await res.json()) as ManuscriptDoc
    }
  }
  ```

## Adding a New API (Python pattern)
- Create `schema/<domain>.py` with clear `BaseModel` DTOs.
- Add `routers/<domain>/<feature>.py` with `APIRouter`, summary/description, and precise types. Keep side-effects in services.
- Include router in `api.py`.

Example (Python)
```py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/analysis", tags=["analysis"])

class ExtractRequest(BaseModel):
    text: str = Field(..., min_length=1, description="원문 텍스트")

class ExtractResponse(BaseModel):
    categories: dict[str, list[str]]

@router.post("/extract", response_model=ExtractResponse, summary="표현 추출")
async def extract(payload: ExtractRequest) -> ExtractResponse:
    # call analyzer layer (pure)
    data = {"example": ["표현1", "표현2"]}
    if not data:
        raise HTTPException(500, "추출 실패")
    return ExtractResponse(categories=data)
```

## Constants & Naming
- Extract magic numbers to constants (e.g., `MAX_TEXT_LEN`, `API_DELAY_EXPR`, `API_DELAY_TMPL`).
- Booleans use `is_` prefix in Python and `is` prefix in TS.
- Arrays end with `List` in TS (`keywordList`), and be explicit in Python (`keywords: list[str]`).
- Converter/collection ops: use `convert*`, `filter*`, `find*` prefixes.

## Data Contracts (Mongo Collections → TS Types)
- morphemes: `{ timestamp: number, word: string }`
- sentences: `{ timestamp: number, sentence: string }`
- expressions: `{ timestamp: number, category: string, expression: string }`
- parameters: `{ timestamp: number, category: string, parameter: string }`
- subtitles: `{ timestamp: number, subtitles: string[], count?: number }`
- templates: `{ timestamp: string, file_name?: string, templated_text: string }`
- manuscripts: `{ content: string, timestamp: number, engine: string, keyword: string }`

Recommend exposing read-only endpoints for each when needed and consuming via typed TS clients.

## Testing
- Python: `pytest` recommended (not included yet). Add unit tests for `analyzer/` pure functions first.
- TS (consumer): `vitest` or `jest`. Place files under `tests/` mirroring `src/`.

## Quality & Style
- Python
  - Type-hint all functions; keep analyzer functions pure.
  - Small modules, single responsibility; extract duplicate logic.
- TypeScript
  - Strict mode on; ESLint/Prettier; single quotes, no semicolons, 2-space indent.
  - React: functional components, props via `interface`, use `React.Fragment` explicitly, hooks prefixed `use`.

## Troubleshooting
- 404 for CLI entry-point: run `python main.py` (or change `pyproject.toml` to `main:cli`).
- 401/403 from LLM: check `OPENAI_API_KEY` and model names in `_constants/Model.py`.
- Mongo duplicates: unique indexes are created in `MongoDBService.ensure_unique_indexes()`; use `upsert_many_documents` for idempotent writes.

## Roadmap (to align with TS-first)
- Expose OpenAPI-driven SDK for TS (`openapi-typescript`), publish as internal package.
- Add read endpoints to fetch latest aggregates (mirror `get_latest_analysis_data`).
- Introduce `clients/ts/` with FSD structure (`entities/`, `features/`, `views/`, `shared/`).
- Optionally add GraphQL proxy (NestJS) if composition across services is needed.

---

## Agent Working Rules (Operational)
- Do not start servers unless explicitly requested.
- Keep comments minimal; only essential, task-relevant context.
- Extract magic numbers to `_constants/` as `UPPER_SNAKE_CASE`.
- Use shared patterns for exceptions, logging, and settings; avoid ad‑hoc prints or global state.
- Python: absolute imports, full type hints, Pydantic models for IO; keep analyzer functions pure.
- TypeScript consumers: absolute imports, TanStack Query, Jotai for state, `cn` utility for class names, Tailwind v4.

## FastAPI Addendum
- Exceptions: raise domain errors in services, convert to `HTTPException` in routers.
- Logging: prefer a shared logger util (no `print`), level from settings.
- Settings: environment variables via a single config module; do not expose secrets at module import time.

## AI Service Addendum
- Token logging: only when `usage` is present; never log prompts with secrets.
- Concurrency: control via `LLM_CONCURRENCY` (no hardcoding); prefer threadpool/async boundaries at service edge.
- Models/limits: manage exclusively in `_constants/`.

## Pydantic Serialization Note
- Internal Python uses `snake_case`. For TS compatibility, optionally use `Field(serialization_alias="lowerCamel")` and `model_config = {"populate_by_name": True}`.

---

## Frontend (TS) Integration Rules

### Absolute Imports and `cn`
- Configure path alias (e.g., Vite `@/*`). All imports should be absolute.
- Class composition must use `cn` (clsx + tailwind-merge):

```ts
// src/shared/lib/cn/index.ts
import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'
export const cn = (...inputs: ClassValue[]) => twMerge(clsx(inputs))
```

### TanStack Query Baseline
```tsx
// src/app/provider/query-client.tsx
import React from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

export const withQueryClient = (node: React.ReactNode) => {
  const client = new QueryClient()
  return <QueryClientProvider client={client}>{node}</QueryClientProvider>
}
```

### Minimal API Client + Hook
```ts
// src/shared/api/client.ts
export interface ApiClientConfig { baseUrl: string; apiKey?: string }
export const createApiClient = ({ baseUrl, apiKey }: ApiClientConfig) => {
  const headers = (): HeadersInit => ({ 'Content-Type': 'application/json', ...(apiKey ? { Authorization: `Bearer ${apiKey}` } : {}) })
  const post = async <TReq, TRes>(path: string, body: TReq): Promise<TRes> => {
    const res = await fetch(`${baseUrl}${path}`, { method: 'POST', headers: headers(), body: JSON.stringify(body) })
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    return (await res.json()) as TRes
  }
  return { post }
}
```

```ts
// src/entities/manuscript/api/types.ts
export type GenerateRequestDto = { service: 'gpt'|'claude'|'solar'|'gemini'|'gpt_5'; keyword: string; ref: string }
export type ManuscriptDoc = { _id?: string; content: string; timestamp: number; engine: string; keyword: string }
```

```ts
// src/entities/manuscript/hooks/use-generate.ts
import { useMutation } from '@tanstack/react-query'
import type { GenerateRequestDto, ManuscriptDoc } from '@/entities/manuscript/api/types'

export const useGenerateManuscript = (baseUrl: string) => {
  return useMutation<ManuscriptDoc, Error, GenerateRequestDto>({
    mutationFn: async (payload) => {
      const res = await fetch(`${baseUrl}/generate/gpt`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      return (await res.json()) as ManuscriptDoc
    },
  })
}
```

### Jotai: Actions in Hooks, Not Store
```ts
// src/shared/state/manuscript.atoms.ts
import { atom } from 'jotai'
import type { ManuscriptDoc } from '@/entities/manuscript/api/types'
export const manuscriptAtom = atom<ManuscriptDoc | undefined>(undefined)
```

```ts
// src/entities/manuscript/hooks/use-manuscript.ts
import React from 'react'
import { useSetAtom } from 'jotai'
import { manuscriptAtom } from '@/shared/state/manuscript.atoms'
import { useGenerateManuscript } from '@/entities/manuscript/hooks/use-generate'

export const useManuscript = (baseUrl: string) => {
  const setManuscript = useSetAtom(manuscriptAtom)
  const gen = useGenerateManuscript(baseUrl)
  const handleGenerate = React.useCallback(async (payload: Parameters<typeof gen.mutateAsync>[0]) => {
    const doc = await gen.mutateAsync(payload)
    setManuscript(doc)
    return doc
  }, [gen, setManuscript])
  return { handleGenerate, isLoading: gen.isPending, error: gen.error }
}
```

### Tailwind v4
- Next.js: https://tailwindcss.com/docs/installation/framework-guides/nextjs
- React/Vue + Vite: https://tailwindcss.com/docs/installation/using-vite
