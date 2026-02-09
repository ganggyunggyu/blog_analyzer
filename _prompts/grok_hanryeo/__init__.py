"""Grok 한려담원 프롬프트 모듈"""

from _prompts.grok_hanryeo.system import get_grok_hanryeo_system_prompt
from _prompts.grok_hanryeo.user import get_grok_hanryeo_user_prompt

__all__ = ["get_grok_hanryeo_system_prompt", "get_grok_hanryeo_user_prompt"]
