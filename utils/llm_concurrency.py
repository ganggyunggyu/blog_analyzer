from __future__ import annotations

import asyncio
import os
from collections.abc import Awaitable, Callable
from typing import TypeVar


LLM_CONCURRENCY = max(1, int(os.getenv("LLM_CONCURRENCY", "3")))
llm_semaphore = asyncio.Semaphore(LLM_CONCURRENCY)

T = TypeVar("T")


def is_llm_path(path: str) -> bool:
    return path.startswith("/generate/")


async def run_with_llm_concurrency_limit(
    operation: Callable[[], Awaitable[T]],
) -> T:
    async with llm_semaphore:
        return await operation()
