from __future__ import annotations

from typing import Any, Generator, Optional, Tuple

from anthropic import Anthropic
from google import genai
from google.genai import types
from openai import OpenAI
from xai_sdk.chat import system as grok_system_message
from xai_sdk.chat import user as grok_user_message

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
from utils.logger import log


MODEL_PRICING: dict[str, Tuple[float, float]] = {
    "gemini-3-flash": (0.50, 3.00),
    "gemini-3-pro": (1.25, 5.00),
    "gemini-2.5-pro": (1.25, 5.00),
    "gpt-5": (1.25, 10.00),
    "gpt-5-mini": (0.25, 2.00),
    "gpt-5-nano": (0.05, 0.40),
    "gpt-4o": (2.50, 10.00),
    "gpt-4.1": (2.00, 8.00),
    "claude-sonnet": (3.00, 15.00),
    "claude-opus": (15.00, 75.00),
    "grok-4-fast": (0.20, 0.50),
    "grok-4-1-fast": (0.20, 0.50),
    "grok-4": (3.00, 15.00),
    "deepseek": (0.28, 0.42),
    "solar": (0.15, 0.60),
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
        raise ValueError(f"AI 클라이언트를 찾을 수 없습니다. (service_type: {ai_service_type})")

    if ai_service_type == "gemini":
        response = client.models.generate_content(
            model=model_name,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
            ),
            contents=user_prompt,
        )
        text = getattr(response, "text", "") or ""
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
        usage = getattr(response, "usage", None)
        if usage:
            input_tokens = getattr(usage, "input_tokens", 0) or 0
            output_tokens = getattr(usage, "output_tokens", 0) or 0

    elif ai_service_type == "openai":
        if model_name.startswith("gpt-5") and "chat" not in model_name:
            response = client.responses.create(
                model=model_name,
                instructions=system_prompt,
                input=user_prompt,
                reasoning={"effort": "medium"},
                text={"verbosity": "medium"},
            )
            text = getattr(response, "output_text", "") or ""
            usage = getattr(response, "usage", None)
            if usage:
                input_tokens = getattr(usage, "input_tokens", 0) or 0
                output_tokens = getattr(usage, "output_tokens", 0) or 0
        else:
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
                raise RuntimeError("GPT-4가 유효한 choices/message를 반환하지 않았습니다.")
            text = (choices[0].message.content or "").strip()
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
            raise RuntimeError("DeepSeek이 유효한 choices/message를 반환하지 않았습니다.")
        text = (choices[0].message.content or "").strip()
        usage = getattr(response, "usage", None)
        if usage:
            input_tokens = getattr(usage, "prompt_tokens", 0) or 0
            output_tokens = getattr(usage, "completion_tokens", 0) or 0

    else:
        raise ValueError(f"지원하지 않는 AI 서비스 타입: {ai_service_type}")

    text = text.strip()
    if not text:
        raise RuntimeError("빈 응답을 받았습니다.")

    if input_tokens > 0 or output_tokens > 0:
        print_token_cost(model_name, input_tokens, output_tokens)

    return text


def call_ai_stream(
    model_name: str,
    system_prompt: str,
    user_prompt: str,
    max_tokens: int = 4096,
) -> Generator[str, None, None]:
    """
    스트리밍 AI 호출 함수 - SSE 형식으로 청크 단위 응답

    Args:
        model_name: 사용할 모델 이름
        system_prompt: 시스템 프롬프트
        user_prompt: 유저 프롬프트
        max_tokens: 최대 토큰 수

    Yields:
        str: 텍스트 청크 (SSE data 형식)
    """
    ai_service_type = get_ai_service_type(model_name)
    validate_api_key(ai_service_type)

    client = get_ai_client(ai_service_type)
    if not client:
        raise ValueError(f"AI 클라이언트를 찾을 수 없습니다. (service_type: {ai_service_type})")

    if ai_service_type == "openai" and (not model_name.startswith("gpt-5") or "chat" in model_name):
        stream = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=max_tokens,
            stream=True,
        )
        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield f"data: {chunk.choices[0].delta.content}\n\n"
        yield "data: [DONE]\n\n"

    elif ai_service_type == "claude":
        with client.messages.stream(
            model=model_name,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
            max_tokens=max_tokens,
        ) as stream:
            for text in stream.text_stream:
                yield f"data: {text}\n\n"
        yield "data: [DONE]\n\n"

    elif ai_service_type == "gemini":
        response = client.models.generate_content_stream(
            model=model_name,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
            ),
            contents=user_prompt,
        )
        for chunk in response:
            if hasattr(chunk, "text") and chunk.text:
                yield f"data: {chunk.text}\n\n"
        yield "data: [DONE]\n\n"

    elif ai_service_type == "deepseek":
        stream = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            stream=True,
        )
        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield f"data: {chunk.choices[0].delta.content}\n\n"
        yield "data: [DONE]\n\n"

    elif ai_service_type == "solar":
        stream = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt + system_prompt},
            ],
            stream=True,
        )
        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield f"data: {chunk.choices[0].delta.content}\n\n"
        yield "data: [DONE]\n\n"

    elif ai_service_type == "grok":
        chat_session = client.chat.create(model=model_name)
        chat_session.append(grok_system_message(system_prompt))
        chat_session.append(grok_user_message(user_prompt))
        response = chat_session.sample()
        text = getattr(response, "content", "") or ""
        chunk_size = 20
        for i in range(0, len(text), chunk_size):
            yield f"data: {text[i:i+chunk_size]}\n\n"
        yield "data: [DONE]\n\n"

    elif ai_service_type == "openai" and model_name.startswith("gpt-5") and "chat" not in model_name:
        response = client.responses.create(
            model=model_name,
            instructions=system_prompt,
            input=user_prompt,
            reasoning={"effort": "medium"},
            text={"verbosity": "medium"},
        )
        text = getattr(response, "output_text", "") or ""
        chunk_size = 20
        for i in range(0, len(text), chunk_size):
            yield f"data: {text[i:i+chunk_size]}\n\n"
        yield "data: [DONE]\n\n"

    else:
        raise ValueError(f"지원하지 않는 AI 서비스 타입: {ai_service_type}")


__all__ = [
    "call_ai",
    "call_ai_stream",
    "get_ai_client",
    "get_ai_service_type",
    "get_model_pricing",
    "print_token_cost",
    "validate_api_key",
]
