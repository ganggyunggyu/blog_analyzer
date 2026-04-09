"""Blog Filler Restaurant - 맛집/관광지 블로그 원고 서비스 (grok급 SEO)"""

from __future__ import annotations

from _constants.Model import Model
from _prompts.blog_filler.restaurant import (
    get_blog_filler_restaurant_system_prompt,
    get_blog_filler_restaurant_user_prompt,
    is_list_keyword,
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
    """맛집/관광지 블로그 원고 생성 (상세리뷰 or 리스트형 자동 감지)"""

    keyword = user_instructions.strip()
    if not keyword:
        raise ValueError("키워드가 없습니다.")

    is_list = is_list_keyword(keyword)
    area_name, pen_name, restaurants, count = get_restaurants_for_keyword(keyword)

    mode_label = f"리스트형({count}곳)" if is_list else "상세리뷰(1곳)"
    log.info(f"맛집 모드={mode_label} 지역={area_name} 필명={pen_name} 데이터={len(restaurants)}개")

    restaurants_text = format_restaurants_for_prompt(restaurants)

    system = get_blog_filler_restaurant_system_prompt(pen_name=pen_name, is_list=is_list)
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
