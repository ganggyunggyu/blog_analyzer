"""대댓글 생성 서비스 - 심플 버전"""

from __future__ import annotations

from _constants.Model import Model
from _prompts.viral import (
    get_recomment_system_prompt,
    get_recomment_user_prompt,
)
from utils.ai_client_factory import call_ai


MODEL_NAME: str = Model.GROK_4_1_NON_RES


def generate_recomment(
    parent_comment: str,
    content: str = "",
) -> dict:
    """대댓글 생성"""
    if not parent_comment or not parent_comment.strip():
        raise ValueError("원댓글 내용이 없습니다.")

    system_prompt = get_recomment_system_prompt()
    user_prompt = get_recomment_user_prompt(
        parent_comment=parent_comment,
        post_content=content,
    )

    comment = call_ai(
        model_name=MODEL_NAME,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
    )

    return {
        "comment": comment,
        "model": MODEL_NAME,
    }
