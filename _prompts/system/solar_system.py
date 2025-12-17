"""Solar Pro 2 전용 프롬프트 (Grok 프롬프트 재사용)"""

from _prompts.system.grok_system import get_grok_system_prompt
from _prompts.user.grok_user import get_grok_user_prompt


def get_solar_system_prompt(keyword: str, category: str) -> str:
    """Solar 시스템 프롬프트 반환 (Grok 시스템 프롬프트 사용)"""
    return get_grok_system_prompt(keyword=keyword, category=category)


def get_solar_user_prompt(keyword: str, note: str, ref: str) -> str:
    """Solar 유저 프롬프트 반환 (Grok 유저 프롬프트 사용)"""
    return get_grok_user_prompt(keyword=keyword, note=note, ref=ref)
