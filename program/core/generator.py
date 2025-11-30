from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from typing import Callable

project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from llm.grok_service import grok_gen
from llm.claude_service import claude_gen
from llm.gpt_4_v3_service import gpt_4_v3_gen
from llm.gemini_3_pro_service import gemini_3_pro_gen
from llm.gemini_service import gemini_gen
from llm.restaurant_service import restaurant_gen
from llm.restaurant_gpt5_service import restaurant_gpt5_gen
from llm.restaurant_claude_service import restaurant_claude_gen
from llm.restaurant_grok_service import restaurant_grok_gen
from llm.chunk_service import chunk_gen
from llm.clean_service import clean_gen
from llm.kkk_service import kkk_gen
from utils.get_category_db_name import get_category_db_name


class Generator:
    ENGINES: dict[str, Callable[[str, str, str], str]] = {
        "Grok": grok_gen,
        "Claude": claude_gen,
        "GPT-4": gpt_4_v3_gen,
        "Gemini 3 Pro": gemini_3_pro_gen,
        "Gemini": gemini_gen,
        "KKK (Multi-AI)": kkk_gen,
        "Restaurant (Gemini)": restaurant_gen,
        "Restaurant (GPT-5)": restaurant_gpt5_gen,
        "Restaurant (Claude)": restaurant_claude_gen,
        "Restaurant (Grok)": restaurant_grok_gen,
        "Chunk": chunk_gen,
        "Clean": clean_gen,
    }

    @classmethod
    def get_engine_names(cls) -> list[str]:
        return list(cls.ENGINES.keys())

    @classmethod
    def _get_category(cls, keyword: str, ref: str = "") -> str:
        text = keyword + ref
        try:
            return asyncio.run(get_category_db_name(keyword=text))
        except Exception:
            return "기타"

    @classmethod
    def generate(
        cls,
        engine: str,
        keyword: str,
        ref: str = "",
    ) -> tuple[str, str]:
        if engine not in cls.ENGINES:
            raise ValueError(f"지원하지 않는 엔진: {engine}")

        category = cls._get_category(keyword, ref)
        service_fn = cls.ENGINES[engine]
        result = service_fn(keyword, ref, category)

        return result, category
