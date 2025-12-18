from __future__ import annotations
from typing import Optional, Dict, Any

from anthropic import Anthropic
from openai import OpenAI
from xai_sdk.chat import system as grok_system_message
from xai_sdk.chat import user as grok_user_message
from google import genai
from google.genai import types

from config import (
    CLAUDE_API_KEY,
    DEEPSEEK_API_KEY,
    GEMINI_API_KEY,
    GROK_API_KEY,
    OPENAI_API_KEY,
    UPSTAGE_API_KEY,
    deepseek_client,
    grok_client,
    solar_client,
)


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
    elif model_name.startswith("solar"):
        return "solar"
    elif model_name.startswith("grok"):
        return "grok"
    elif model_name.startswith("deepseek"):
        return "deepseek"
    else:
        return "openai"


def get_ai_client(ai_service_type: str) -> Optional[Any]:
    """
    AI 서비스 타입에 맞는 클라이언트 반환

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
        return Anthropic(api_key=CLAUDE_API_KEY) if CLAUDE_API_KEY else None
    elif ai_service_type == "solar":
        return solar_client
    elif ai_service_type == "grok":
        return grok_client
    elif ai_service_type == "deepseek":
        return deepseek_client
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
            raise ValueError(
                "GEMINI_API_KEY가 설정되어 있지 않습니다. .env를 확인하세요."
            )
    elif ai_service_type == "openai":
        if not OPENAI_API_KEY:
            raise ValueError(
                "OPENAI_API_KEY가 설정되어 있지 않습니다. .env를 확인하세요."
            )
    elif ai_service_type == "grok":
        if not GROK_API_KEY:
            raise ValueError(
                "GROK_API_KEY가 설정되어 있지 않습니다. .env를 확인하세요."
            )
    elif ai_service_type == "claude":
        if not CLAUDE_API_KEY:
            raise ValueError(
                "CLAUDE_API_KEY가 설정되어 있지 않습니다. .env를 확인하세요."
            )
    elif ai_service_type == "deepseek":
        if not DEEPSEEK_API_KEY:
            raise ValueError(
                "DEEPSEEK_API_KEY가 설정되어 있지 않습니다. .env를 확인하세요."
            )


# 모델별 가격 (USD per 1M tokens) - input/output
# 2025년 12월 기준 최신 가격
MODEL_PRICING = {
    # Gemini (per 1M tokens)
    "gemini-3-flash": (0.50, 3.00),      # Gemini 3 Flash
    "gemini-3-pro": (1.25, 5.00),        # Gemini 3 Pro (추정)
    "gemini-2.5-pro": (1.25, 5.00),      # Gemini 2.5 Pro
    # OpenAI (per 1M tokens)
    "gpt-5": (1.25, 10.00),              # GPT-5
    "gpt-5-mini": (0.25, 2.00),          # GPT-5 Mini
    "gpt-5-nano": (0.05, 0.40),          # GPT-5 Nano
    "gpt-4o": (2.50, 10.00),             # GPT-4o
    "gpt-4.1": (2.00, 8.00),             # GPT-4.1
    # Claude (per 1M tokens)
    "claude-sonnet": (3.00, 15.00),      # Claude Sonnet 4.5
    "claude-opus": (15.00, 75.00),       # Claude Opus 4.5
    # Grok (per 1M tokens)
    "grok-4-fast": (0.20, 0.50),         # Grok 4 Fast (reasoning/non-reasoning)
    "grok-4-1-fast": (0.20, 0.50),       # Grok 4.1 Fast
    "grok-4": (3.00, 15.00),             # Grok 4 Standard
    # DeepSeek (per 1M tokens) - cache miss 기준
    "deepseek": (0.28, 0.42),            # DeepSeek V3.2
    # Solar (per 1M tokens)
    "solar": (0.15, 0.60),               # Solar Pro
}


def get_model_pricing(model_name: str) -> tuple:
    """모델명에서 가격 정보 가져오기"""
    for key, price in MODEL_PRICING.items():
        if key in model_name.lower():
            return price
    return (0.01, 0.03)  # 기본값


def print_token_cost(model_name: str, input_tokens: int, output_tokens: int) -> None:
    """토큰 사용량 및 비용 출력"""
    input_price, output_price = get_model_pricing(model_name)

    # 가격은 per 1M tokens 기준
    input_cost = (input_tokens / 1_000_000) * input_price
    output_cost = (output_tokens / 1_000_000) * output_price
    total_cost = input_cost + output_cost
    total_krw = total_cost * 1400

    print(f"[토큰] in: {input_tokens:,} | out: {output_tokens:,} | total: {input_tokens + output_tokens:,}")
    print(f"[비용] ${total_cost:.6f} (약 {total_krw:.2f}원)")


def call_ai(
    model_name: str,
    system_prompt: str,
    user_prompt: str,
    max_tokens: int = 4096,
) -> str:
    """
    통합 AI 호출 함수 - 모델명에 따라 적절한 AI 서비스 호출

    Args:
        model_name: 사용할 모델 이름
        system_prompt: 시스템 프롬프트
        user_prompt: 유저 프롬프트
        max_tokens: 최대 토큰 수 (기본값: 4096)

    Returns:
        AI 응답 텍스트

    Raises:
        ValueError: API 키가 없거나 클라이언트를 찾을 수 없는 경우
        RuntimeError: 빈 응답을 받은 경우
    """
    ai_service_type = get_ai_service_type(model_name)
    validate_api_key(ai_service_type)

    input_tokens = 0
    output_tokens = 0

    client = get_ai_client(ai_service_type)
    if not client:
        raise ValueError(
            f"AI 클라이언트를 찾을 수 없습니다. (service_type: {ai_service_type})"
        )

    # AI 서비스별 호출
    if ai_service_type == "gemini":
        response = client.models.generate_content(
            model=model_name,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
            ),
            contents=user_prompt,
        )
        text = getattr(response, "text", "") or ""
        # Gemini 토큰
        usage = getattr(response, "usage_metadata", None)
        if usage:
            input_tokens = getattr(usage, "prompt_token_count", 0) or 0
            output_tokens = getattr(usage, "candidates_token_count", 0) or 0

    elif ai_service_type == "claude":
        response = client.messages.create(
            model=model_name,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
            max_tokens=max_tokens,
        )
        content_blocks = getattr(response, "content", [])
        text = getattr(content_blocks[0], "text", "") if content_blocks else ""
        # Claude 토큰
        usage = getattr(response, "usage", None)
        if usage:
            input_tokens = getattr(usage, "input_tokens", 0) or 0
            output_tokens = getattr(usage, "output_tokens", 0) or 0

    elif ai_service_type == "openai":
        if model_name.startswith("gpt-5"):
            # GPT-5 시리즈: Responses API
            response = client.responses.create(
                model=model_name,
                instructions=system_prompt,
                input=user_prompt,
                reasoning={"effort": "medium"},
                text={"verbosity": "medium"},
            )
            text = getattr(response, "output_text", "") or ""
            # GPT-5 토큰
            usage = getattr(response, "usage", None)
            if usage:
                input_tokens = getattr(usage, "input_tokens", 0) or 0
                output_tokens = getattr(usage, "output_tokens", 0) or 0
        else:
            # GPT-4 시리즈: Chat Completions API
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=max_tokens,
            )
            choices = getattr(response, "choices", []) or []
            if not choices or not getattr(choices[0], "message", None):
                raise RuntimeError(
                    "GPT-4가 유효한 choices/message를 반환하지 않았습니다."
                )
            text = (choices[0].message.content or "").strip()
            # GPT-4 토큰
            usage = getattr(response, "usage", None)
            if usage:
                input_tokens = getattr(usage, "prompt_tokens", 0) or 0
                output_tokens = getattr(usage, "completion_tokens", 0) or 0

    elif ai_service_type == "solar":
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt + system_prompt},
            ],
            reasoning_effort="high",
        )
        choices = getattr(response, "choices", []) or []
        if not choices or not getattr(choices[0], "message", None):
            raise RuntimeError("SOLAR가 유효한 choices/message를 반환하지 않았습니다.")
        text = (choices[0].message.content or "").strip()
        # Solar 토큰
        usage = getattr(response, "usage", None)
        if usage:
            input_tokens = getattr(usage, "prompt_tokens", 0) or 0
            output_tokens = getattr(usage, "completion_tokens", 0) or 0

    elif ai_service_type == "grok":
        chat_session = client.chat.create(model=model_name)
        chat_session.append(grok_system_message(system_prompt))
        chat_session.append(grok_user_message(user_prompt))
        response = chat_session.sample()
        text = getattr(response, "content", "") or ""
        # Grok 토큰 (SDK에서 지원 시)
        usage = getattr(response, "usage", None)
        if usage:
            input_tokens = getattr(usage, "prompt_tokens", 0) or 0
            output_tokens = getattr(usage, "completion_tokens", 0) or 0

    elif ai_service_type == "deepseek":
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        choices = getattr(response, "choices", []) or []
        if not choices or not getattr(choices[0], "message", None):
            raise RuntimeError(
                "DeepSeek이 유효한 choices/message를 반환하지 않았습니다."
            )
        text = (choices[0].message.content or "").strip()
        # DeepSeek 토큰
        usage = getattr(response, "usage", None)
        if usage:
            input_tokens = getattr(usage, "prompt_tokens", 0) or 0
            output_tokens = getattr(usage, "completion_tokens", 0) or 0

    else:
        raise ValueError(f"지원하지 않는 AI 서비스 타입: {ai_service_type}")

    text = text.strip()
    if not text:
        raise RuntimeError("빈 응답을 받았습니다.")

    # 토큰 비용 출력
    if input_tokens > 0 or output_tokens > 0:
        print_token_cost(model_name, input_tokens, output_tokens)

    return text
