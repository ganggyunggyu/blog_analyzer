from __future__ import annotations

from typing import Any, Optional, Tuple

from anthropic import Anthropic
from google import genai
from openai import OpenAI

from config import (
    CLAUDE_API_KEY,
    DEEPSEEK_API_KEY,
    GEMINI_API_KEY,
    GROK_API_KEY,
    MINIMAX_API_KEY,
    MOONSHOT_API_KEY,
    OPENAI_API_KEY,
    UPSTAGE_API_KEY,
    deepseek_client,
    grok_client,
    minimax_client,
    moonshot_client,
    solar_client,
)
from utils.logger import log


MODEL_PRICING: dict[str, Tuple[float, float]] = {
    "gemini-3-flash": (0.50, 3.00),
    "gemini-3-pro": (1.25, 5.00),
    "gemini-2.5-pro": (1.25, 5.00),
    "gpt-5": (1.25, 10.00),
    "gpt-5.4-mini": (0.75, 4.50),
    "gpt-5-mini": (0.25, 2.00),
    "gpt-5-nano": (0.05, 0.40),
    "gpt-4o": (2.50, 10.00),
    "gpt-4.1": (2.00, 8.00),
    "claude-sonnet": (3.00, 15.00),
    "claude-opus": (15.00, 75.00),
    "grok-4-fast": (0.20, 0.50),
    "grok-4-1-fast": (0.20, 0.50),
    "grok-4": (3.00, 15.00),
    "deepseek-v4-flash": (0.14, 0.28),
    "deepseek-v4-pro": (1.74, 3.48),
    "deepseek": (0.14, 0.28),
    "solar": (0.15, 0.60),
    "kimi": (0.60, 2.50),
    "minimax": (1.00, 5.00),
}


def get_ai_service_type(model_name: str) -> str:
    """
    모델명으로부터 AI 서비스 타입을 결정

    Args:
        model_name: 모델 이름 (예: "gemini-2.0-flash", "claude-3-sonnet", "gpt-4")

    Returns:
        AI 서비스 타입 ("gemini", "claude", "solar", "grok", "openai")
    """
    if model_name.startswith("gemini"):
        return "gemini"
    elif model_name.startswith("claude"):
        return "claude"
    elif model_name.startswith("MiniMax"):
        return "minimax"
    elif model_name.startswith("solar"):
        return "solar"
    elif model_name.startswith("grok"):
        return "grok"
    elif model_name.startswith("deepseek"):
        return "deepseek"
    elif model_name.startswith("kimi"):
        return "kimi"
    else:
        return "openai"


def get_ai_client(ai_service_type: str) -> Optional[Any]:
    """
    AI 서비스 타입에 맞는 클라이언트를 반환

    Args:
        ai_service_type: AI 서비스 타입

    Returns:
        해당 AI 서비스 클라이언트
    """
    if ai_service_type == "openai":
        return OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None
    elif ai_service_type == "gemini":
        return genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None
    elif ai_service_type == "claude":
        return Anthropic(api_key=CLAUDE_API_KEY, timeout=600.0) if CLAUDE_API_KEY else None
    elif ai_service_type == "minimax":
        return minimax_client
    elif ai_service_type == "solar":
        return solar_client
    elif ai_service_type == "grok":
        return grok_client
    elif ai_service_type == "deepseek":
        return deepseek_client
    elif ai_service_type == "kimi":
        return moonshot_client
    return None


def validate_api_key(ai_service_type: str) -> None:
    """
    AI 서비스 타입에 맞는 API 키가 설정되어 있는지 확인

    Args:
        ai_service_type: AI 서비스 타입

    Raises:
        ValueError: API 키가 설정되어 있지 않은 경우
    """
    if ai_service_type == "solar":
        if not UPSTAGE_API_KEY:
            raise ValueError("UPSTAGE_API_KEY가 설정되어 있지 않습니다.")
    elif ai_service_type == "gemini":
        if not GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY가 설정되어 있지 않습니다. .env를 확인하세요.")
    elif ai_service_type == "openai":
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY가 설정되어 있지 않습니다. .env를 확인하세요.")
    elif ai_service_type == "grok":
        if not GROK_API_KEY:
            raise ValueError("GROK_API_KEY가 설정되어 있지 않습니다. .env를 확인하세요.")
    elif ai_service_type == "claude":
        if not CLAUDE_API_KEY:
            raise ValueError("CLAUDE_API_KEY가 설정되어 있지 않습니다. .env를 확인하세요.")
    elif ai_service_type == "deepseek":
        if not DEEPSEEK_API_KEY:
            raise ValueError("DEEPSEEK_API_KEY가 설정되어 있지 않습니다. .env를 확인하세요.")
    elif ai_service_type == "minimax":
        if not MINIMAX_API_KEY:
            raise ValueError("MINIMAX_API_KEY가 설정되어 있지 않습니다. .env를 확인하세요.")
    elif ai_service_type == "kimi":
        if not MOONSHOT_API_KEY:
            raise ValueError("MOONSHOT_API_KEY가 설정되어 있지 않습니다. .env를 확인하세요.")


def get_model_pricing(model_name: str) -> Tuple[float, float]:
    """모델명에서 가격 정보 가져오기"""
    for key, price in MODEL_PRICING.items():
        if key in model_name.lower():
            return price
    return (0.01, 0.03)


def print_token_cost(model_name: str, input_tokens: int, output_tokens: int) -> None:
    """토큰 사용량 및 비용 출력"""
    input_price, output_price = get_model_pricing(model_name)

    input_cost = (input_tokens / 1_000_000) * input_price
    output_cost = (output_tokens / 1_000_000) * output_price
    total_cost = input_cost + output_cost
    total_krw = total_cost * 1400

    log.info(
        f"토큰 in={input_tokens:,} out={output_tokens:,} | 비용=${total_cost:.4f} ({total_krw:.0f}원)"
    )


__all__ = [
    "MODEL_PRICING",
    "get_ai_client",
    "get_ai_service_type",
    "get_model_pricing",
    "print_token_cost",
    "validate_api_key",
]
