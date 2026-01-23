"""맛집 후기 생성 서비스 (Gemini 3 Pro)"""

from __future__ import annotations

from _constants.Model import Model
from utils.text_cleaner import comprehensive_text_clean
from utils.ai_client_factory import call_ai
from utils.logger import log


MODEL_NAME: str = Model.GEMINI_3_PRO


SYSTEM_PROMPT = """
"""


def get_user_prompt(keyword: str, ref: str = "") -> str:
    prompt = f"""
{keyword}
"""
    if ref:
        prompt += f"\n\n참조:\n{ref}"
    return prompt.strip()


def restaurant_gemini_gen(keyword: str, ref: str = "") -> dict:
    """맛집 후기 생성

    Args:
        keyword: 맛집 정보 (fullText)
        ref: 참조 원고

    Returns:
        생성 결과
    """
    if not keyword:
        raise ValueError("키워드가 필요합니다.")

    system = SYSTEM_PROMPT.strip()
    user = get_user_prompt(keyword=keyword, ref=ref)

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
        "model": MODEL_NAME,
        "char_count": len(text.replace(" ", "")),
    }
