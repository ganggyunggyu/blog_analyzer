"""바이럴 프롬프트 패키지 - 18종 페르소나 연동"""

from _prompts.viral.post_prompt import (
    POST_SYSTEM_PROMPT,
    PERSONAS,
    get_post_system_prompt,
    get_post_user_prompt,
    get_persona,
)

from _prompts.viral.comment_prompt import (
    COMMENT_SYSTEM_PROMPT,
    COMMENT_PERSONAS,
    get_comment_system_prompt,
    get_comment_user_prompt,
    get_comment_persona,
)

from _prompts.viral.recomment_prompt import (
    RECOMMENT_SYSTEM_PROMPT,
    RECOMMENT_PERSONAS,
    get_recomment_system_prompt,
    get_recomment_user_prompt,
    get_recomment_persona,
)

__all__ = [
    # 글 작성
    "POST_SYSTEM_PROMPT",
    "PERSONAS",
    "get_post_system_prompt",
    "get_post_user_prompt",
    "get_persona",
    # 댓글 작성
    "COMMENT_SYSTEM_PROMPT",
    "COMMENT_PERSONAS",
    "get_comment_system_prompt",
    "get_comment_user_prompt",
    "get_comment_persona",
    # 대댓글 작성
    "RECOMMENT_SYSTEM_PROMPT",
    "RECOMMENT_PERSONAS",
    "get_recomment_system_prompt",
    "get_recomment_user_prompt",
    "get_recomment_persona",
]
