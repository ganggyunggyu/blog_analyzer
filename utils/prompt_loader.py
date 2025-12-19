"""프롬프트 로더 유틸리티

GitHub Raw URL에서 프롬프트 파일을 로드하고 Jinja2 변수 치환을 수행합니다.

Usage:
    from utils.prompt_loader import load_prompt, render_prompt

    # 단순 로드
    prompt = load_prompt("system/gemini/system.j2")

    # 변수 치환
    prompt = render_prompt("system/gpt/user.j2", keyword="리쥬란", ref="참조원고...")
"""

from __future__ import annotations
import os
import re
from functools import lru_cache
from typing import Optional

import requests

# GitHub 레포 설정 (나중에 실제 레포로 변경)
GITHUB_REPO = "21lab/blog-prompts"
GITHUB_BRANCH = "main"
BASE_URL = f"https://raw.githubusercontent.com/{GITHUB_REPO}/{GITHUB_BRANCH}"

# 로컬 폴더 경로 (개발용)
LOCAL_PROMPTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "21lab-prompts")

# 환경변수로 모드 전환 (local / remote)
PROMPT_MODE = os.getenv("PROMPT_MODE", "local")

@lru_cache(maxsize=100)
def _fetch_remote(path: str) -> str:
    """GitHub에서 프롬프트 파일 fetch (캐싱됨)"""
    url = f"{BASE_URL}/{path}"
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    return response.text

def _load_local(path: str) -> str:
    """로컬 파일에서 프롬프트 로드"""
    file_path = os.path.join(LOCAL_PROMPTS_DIR, path)
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"프롬프트 파일을 찾을 수 없습니다: {file_path}")
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()

def load_prompt(path: str, mode: Optional[str] = None) -> str:
    """프롬프트 파일 로드

    Args:
        path: 프롬프트 파일 경로 (예: "system/gemini/system.j2")
        mode: 로드 모드 ("local" 또는 "remote"), None이면 환경변수 사용

    Returns:
        프롬프트 텍스트

    Examples:
        >>> load_prompt("category/리쥬란.j2")
        >>> load_prompt("system/gpt/system.j2", mode="local")
    """
    use_mode = mode or PROMPT_MODE

    if use_mode == "local":
        return _load_local(path)
    else:
        return _fetch_remote(path)

def render_prompt(path: str, mode: Optional[str] = None, **kwargs) -> str:
    """프롬프트 로드 후 변수 치환

    Args:
        path: 프롬프트 파일 경로
        mode: 로드 모드
        **kwargs: 치환할 변수들

    Returns:
        변수가 치환된 프롬프트 텍스트

    Examples:
        >>> render_prompt("system/gpt/user.j2", keyword="리쥬란", ref="참조원고")
    """
    template = load_prompt(path, mode)

    # Jinja2 스타일 변수 치환 ({{변수}})
    for key, value in kwargs.items():
        pattern = r"\{\{\s*" + re.escape(key) + r"\s*\}\}"
        template = re.sub(pattern, str(value) if value else "", template)

    return template

def clear_cache():
    """프롬프트 캐시 초기화 (개발용)"""
    _fetch_remote.cache_clear()

# 편의 함수들
def get_system_prompt(model: str, variant: str = "system", **kwargs) -> str:
    """시스템 프롬프트 로드

    Args:
        model: 모델명 (gemini, gpt, claude, grok, deepseek)
        variant: 변형 (system, new_system, flash_system 등)
        **kwargs: 변수들

    Examples:
        >>> get_system_prompt("gemini", "new_system", keyword="리쥬란")
    """
    path = f"system/{model}/{variant}.j2"
    return render_prompt(path, **kwargs)

def get_user_prompt(model: str, variant: str = "user", **kwargs) -> str:
    """유저 프롬프트 로드

    Args:
        model: 모델명
        variant: 변형 (user, new_user, flash_user 등)
        **kwargs: 변수들

    Examples:
        >>> get_user_prompt("gpt", keyword="마운자로", ref="참조원고")
    """
    path = f"system/{model}/{variant}.j2"
    return render_prompt(path, **kwargs)

def get_category_prompt(category: str, **kwargs) -> str:
    """카테고리 프롬프트 로드

    Args:
        category: 카테고리명 (리쥬란, 미용학원 등)
        **kwargs: 변수들

    Examples:
        >>> get_category_prompt("리쥬란")
    """
    path = f"category/{category}.j2"
    return render_prompt(path, **kwargs)

def get_rule(rule_name: str) -> str:
    """규칙 프롬프트 로드

    Args:
        rule_name: 규칙명 (taboo_rules, line_break_rules 등)

    Examples:
        >>> get_rule("taboo_rules")
    """
    path = f"rules/{rule_name}.txt"
    return load_prompt(path)
