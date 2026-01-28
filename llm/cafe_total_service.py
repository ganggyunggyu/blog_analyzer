"""카페 글 종합 생성기 - 모델 선택 가능"""

from __future__ import annotations

from _constants.Model import Model
from utils.ai_client_factory import call_ai
from utils.query_parser import parse_query
from utils.text_cleaner import comprehensive_text_clean
from utils.logger import log


DEFAULT_MODEL: str = Model.GEMINI_3_PRO


SYSTEM_PROMPT = """
"""

USER_PROMPT_TEMPLATE = """{keyword}"""


def cafe_total_gen(
    user_instructions: str,
    ref: str = "",
    model_name: str = "",
) -> dict:
    """카페 글 종합 생성

    Args:
        user_instructions: 키워드/지시사항
        ref: 참조 원고
        model_name: 사용할 모델명 (빈 값이면 기본 모델 사용)

    Returns:
        생성 결과
    """
    parsed = parse_query(user_instructions)
    keyword = parsed.get("keyword", "")
    note = parsed.get("note", "")

    if not keyword:
        raise ValueError("키워드가 없습니다.")

    model = model_name if model_name else DEFAULT_MODEL

    system = SYSTEM_PROMPT.format(keyword=keyword, note=note)
    user = USER_PROMPT_TEMPLATE.format(keyword=keyword, note=note)

    if ref:
        user = f"{user}\n\n참조 원고:\n{ref}"

    log.info(f"모델={model} sys={len(system)} user={len(user)}")

    try:
        text = call_ai(
            model_name=model,
            system_prompt=system,
            user_prompt=user,
        )
    except Exception as e:
        log.error(f"call_ai 에러: {e}")
        raise

    log.info(f"응답 len={len(text)}")

    text = comprehensive_text_clean(text)

    return {
        "content": text,
        "keyword": keyword,
        "model": model,
        "char_count": len(text.replace(" ", "")),
    }
