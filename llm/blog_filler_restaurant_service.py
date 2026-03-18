"""Blog Filler Restaurant - 맛집 리스트 블로그 글밥 전용 서비스"""

from __future__ import annotations

from _constants.Model import Model
from _prompts.blog_filler.restaurant import (
    get_blog_filler_restaurant_system_prompt,
    get_blog_filler_restaurant_user_prompt,
)
from _prompts.blog_filler.restaurant_data import (
    get_restaurants_for_keyword,
    format_restaurants_for_prompt,
)
from utils.text_cleaner import comprehensive_text_clean, remove_markdown
from utils.ai_client_factory import call_ai
from utils.logger import log


MODEL_NAME: str = Model.CLAUDE_SONNET_4_6


def blog_filler_restaurant_gen(user_instructions: str, ref: str = "", category: str = "") -> str:
    """맛집 리스트 블로그 글밥 생성"""

    keyword = user_instructions.strip()
    if not keyword:
        raise ValueError("키워드가 없습니다.")

    area_name, pen_name, restaurants, count = get_restaurants_for_keyword(keyword)

    log.info(f"맛집 지역={area_name} 필명={pen_name} 데이터={len(restaurants)}개 요청={count}선")

    restaurants_text = format_restaurants_for_prompt(restaurants)

    system = get_blog_filler_restaurant_system_prompt(pen_name=pen_name)
    user = get_blog_filler_restaurant_user_prompt(
        keyword=keyword,
        area_name=area_name,
        pen_name=pen_name,
        restaurants_text=restaurants_text,
        count=count,
    )

    log.info(f"프롬프트 sys={len(system)} user={len(user)}")

    try:
        text = call_ai(
            model_name=MODEL_NAME,
            system_prompt=system,
            user_prompt=user,
        )
    except Exception as e:
        log.error(f"call_ai 에러: {e}")
        raise

    log.info(f"응답 len={len(text)}")

    text = remove_markdown(text)
    text = comprehensive_text_clean(text)

    return text
