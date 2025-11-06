from __future__ import annotations
from ai_lib.parse_food_review import parse_food_review


async def requirement_analysis_gen(user_instructions: str) -> str:

    text = await parse_food_review(text=user_instructions)
    return text
