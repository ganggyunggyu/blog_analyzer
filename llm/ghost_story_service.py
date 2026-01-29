"""괴담 생성 서비스"""

from __future__ import annotations

from _prompts.gemini.ghost_story_system import get_ghost_story_system_prompt
from _prompts.gemini.ghost_story_user import get_ghost_story_user_prompt
from _constants.Model import Model
from utils.text_cleaner import comprehensive_text_clean
from utils.ai_client_factory import call_ai
from utils.logger import log


MODEL_NAME: str = Model.GEMINI_3_PRO


def generate_ghost_story(
    keyword: str,
    setting: str = "",
    style: str = "",
) -> dict:
    """괴담 생성

    Args:
        keyword: 괴담 주제/키워드
        setting: 배경 설정
        style: 스타일

    Returns:
        생성된 괴담 정보
    """
    if not keyword:
        raise ValueError("키워드가 필요합니다.")

    system = get_ghost_story_system_prompt()
    user = get_ghost_story_user_prompt(keyword=keyword, setting=setting, style=style)

    log.info(f"프롬프트 sys={len(system)} user={len(user)}")

    try:
        text = call_ai(model_name=MODEL_NAME, system_prompt=system, user_prompt=user)
    except Exception as e:
        log.error(f"call_ai 에러: {e}")
        raise

    log.info(f"응답 len={len(text)}")

    text = comprehensive_text_clean(text)

    return {
        "content": text,
        "keyword": keyword,
        "setting": setting,
        "style": style,
        "model": MODEL_NAME,
        "char_count": len(text.replace(" ", "")),
    }
