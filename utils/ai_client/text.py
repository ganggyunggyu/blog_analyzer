from __future__ import annotations

from typing import Generator, Optional

from utils.ai_client.text_providers import (
    call_anthropic_text,
    call_chat_completion_text,
    call_gemini_text,
    call_grok_text,
    call_openai_text,
    stream_anthropic_text,
    stream_chat_completion_text,
    stream_gemini_text,
    stream_grok_text,
    stream_openai_text,
)
from utils.ai_client.text_registry import (
    MODEL_PRICING as MODEL_PRICING,
    get_ai_client,
    get_ai_service_type,
    get_model_pricing,
    print_token_cost,
    validate_api_key,
)


def get_deepseek_request_options(model_name: str) -> dict[str, object]:
    if model_name == "deepseek-v4-pro":
        return {
            "reasoning_effort": "high",
            "extra_body": {"thinking": {"type": "enabled"}},
        }

    if model_name in {"deepseek-v4-flash", "deepseek-chat"}:
        return {"extra_body": {"thinking": {"type": "disabled"}}}

    if model_name == "deepseek-reasoner":
        return {
            "reasoning_effort": "high",
            "extra_body": {"thinking": {"type": "enabled"}},
        }

    return {}


def call_ai(
    model_name: str,
    system_prompt: str,
    user_prompt: str,
    max_tokens: int = 4096,
    temperature: Optional[float] = None,
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
        text, input_tokens, output_tokens = call_gemini_text(
            client=client,
            model_name=model_name,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=temperature,
        )

    elif ai_service_type == "claude":
        text, input_tokens, output_tokens = call_anthropic_text(
            client=client,
            model_name=model_name,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=max_tokens,
            temperature=temperature,
        )

    elif ai_service_type == "minimax":
        text, input_tokens, output_tokens = call_anthropic_text(
            client=client,
            model_name=model_name,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=max_tokens,
        )

    elif ai_service_type == "openai":
        text, input_tokens, output_tokens = call_openai_text(
            client=client,
            model_name=model_name,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=max_tokens,
        )

    elif ai_service_type == "solar":
        text, input_tokens, output_tokens = call_chat_completion_text(
            client=client,
            model_name=model_name,
            system_prompt=system_prompt,
            user_prompt=user_prompt + system_prompt,
            provider_name="SOLAR",
            reasoning_effort="high",
        )

    elif ai_service_type == "grok":
        text, input_tokens, output_tokens = call_grok_text(
            client=client,
            model_name=model_name,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )

    elif ai_service_type == "deepseek":
        deepseek_options = get_deepseek_request_options(model_name)
        reasoning_effort = deepseek_options.get("reasoning_effort")
        extra_body = deepseek_options.get("extra_body")
        text, input_tokens, output_tokens = call_chat_completion_text(
            client=client,
            model_name=model_name,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            provider_name="DeepSeek",
            max_tokens=max_tokens,
            reasoning_effort=(
                reasoning_effort if isinstance(reasoning_effort, str) else None
            ),
            extra_body=extra_body if isinstance(extra_body, dict) else None,
        )

    elif ai_service_type == "kimi":
        text, input_tokens, output_tokens = call_chat_completion_text(
            client=client,
            model_name=model_name,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            provider_name="Kimi",
        )

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

    if ai_service_type == "openai":
        yield from stream_openai_text(
            client=client,
            model_name=model_name,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=max_tokens,
        )

    elif ai_service_type == "claude":
        yield from stream_anthropic_text(
            client=client,
            model_name=model_name,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=max_tokens,
        )

    elif ai_service_type == "minimax":
        yield from stream_anthropic_text(
            client=client,
            model_name=model_name,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=max_tokens,
        )

    elif ai_service_type == "gemini":
        yield from stream_gemini_text(
            client=client,
            model_name=model_name,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )

    elif ai_service_type == "deepseek":
        deepseek_options = get_deepseek_request_options(model_name)
        reasoning_effort = deepseek_options.get("reasoning_effort")
        extra_body = deepseek_options.get("extra_body")
        yield from stream_chat_completion_text(
            client=client,
            model_name=model_name,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=max_tokens,
            reasoning_effort=(
                reasoning_effort if isinstance(reasoning_effort, str) else None
            ),
            extra_body=extra_body if isinstance(extra_body, dict) else None,
        )

    elif ai_service_type == "kimi":
        yield from stream_chat_completion_text(
            client=client,
            model_name=model_name,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )

    elif ai_service_type == "solar":
        yield from stream_chat_completion_text(
            client=client,
            model_name=model_name,
            system_prompt=system_prompt,
            user_prompt=user_prompt + system_prompt,
        )

    elif ai_service_type == "grok":
        yield from stream_grok_text(
            client=client,
            model_name=model_name,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )

    else:
        raise ValueError(f"지원하지 않는 AI 서비스 타입: {ai_service_type}")


__all__ = [
    "call_ai",
    "call_ai_stream",
    "get_ai_client",
    "get_deepseek_request_options",
    "get_ai_service_type",
    "get_model_pricing",
    "print_token_cost",
    "validate_api_key",
]
