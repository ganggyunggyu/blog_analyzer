"""대댓글 생성 서비스 - Gemini Flash 기반 (18종 페르소나)"""

from __future__ import annotations
import random

from _constants.Model import Model
from _prompts.viral import (
    get_recomment_system_prompt,
    get_recomment_user_prompt,
    RECOMMENT_PERSONAS,
    get_recomment_persona,
)
from utils.ai_client_factory import call_ai


MODEL_NAME: str = Model.GEMINI_3_FLASH_PREVIEW


def generate_recomment(
    parent_comment: str,
    content: str = "",
    persona_id: int | None = None,
    keyword: str = "",
    keyword_type: str = "자사",
    role: str = "제3자",
    product_name: str = "한려담원 흑염소진액",
) -> dict:
    """대댓글 생성 (18종 페르소나)"""
    if not parent_comment or not parent_comment.strip():
        raise ValueError("원댓글 내용이 없습니다.")

    # 페르소나 선택 (1~18 랜덤 또는 지정)
    if persona_id and persona_id in RECOMMENT_PERSONAS:
        used_id = persona_id
    else:
        used_id = random.randint(1, 18)

    persona = get_recomment_persona(used_id)

    # 새 바이럴 프롬프트 사용
    system_prompt = get_recomment_system_prompt()
    user_prompt = get_recomment_user_prompt(
        parent_comment=parent_comment,
        post_content=content,
        role=role,
        keyword=keyword,
        keyword_type=keyword_type,
        persona_id=used_id,
        product_name=product_name,
    )

    comment = call_ai(
        model_name=MODEL_NAME,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
    )

    return {
        "comment": comment,
        "persona_id": used_id,
        "persona": persona["name"],
        "model": MODEL_NAME,
    }
