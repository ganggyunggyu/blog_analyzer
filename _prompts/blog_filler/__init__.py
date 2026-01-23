"""Blog Filler 프롬프트 패키지"""

from _prompts.blog_filler.system import get_blog_filler_system_prompt
from _prompts.blog_filler.user import get_blog_filler_user_prompt

__all__ = [
    "get_blog_filler_system_prompt",
    "get_blog_filler_user_prompt",
]
