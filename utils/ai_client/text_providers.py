from __future__ import annotations

from typing import Any, Generator, Optional

from google.genai import types
from xai_sdk.chat import system as grok_system_message
from xai_sdk.chat import user as grok_user_message


TextCallResult = tuple[str, int, int]


def _build_anthropic_request(
    model_name: str,
    system_prompt: str,
    user_prompt: str,
    max_tokens: int,
    temperature: Optional[float] = None,
) -> dict[str, Any]:
    request = {
        "model": model_name,
        "messages": [{"role": "user", "content": user_prompt}],
        "max_tokens": max_tokens,
    }
    normalized_system_prompt = system_prompt.strip()
    if normalized_system_prompt:
        request["system"] = normalized_system_prompt
    if temperature is not None:
        request["temperature"] = temperature
    return request


def _build_gemini_config(
    system_prompt: str,
    temperature: Optional[float] = None,
) -> types.GenerateContentConfig:
    config_kwargs: dict[str, Any] = {"system_instruction": system_prompt}
    if temperature is not None:
        config_kwargs["temperature"] = temperature
    return types.GenerateContentConfig(**config_kwargs)


def _build_chat_messages(system_prompt: str, user_prompt: str) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def _extract_anthropic_result(response: Any) -> TextCallResult:
    content_blocks = getattr(response, "content", [])
    text = getattr(content_blocks[0], "text", "") if content_blocks else ""
    usage = getattr(response, "usage", None)
    input_tokens = getattr(usage, "input_tokens", 0) or 0
    output_tokens = getattr(usage, "output_tokens", 0) or 0
    return text, input_tokens, output_tokens


def _extract_chat_completion_result(response: Any, provider_name: str) -> TextCallResult:
    choices = getattr(response, "choices", []) or []
    if not choices or not getattr(choices[0], "message", None):
        raise RuntimeError(f"{provider_name}가 유효한 choices/message를 반환하지 않았습니다.")
    text = (choices[0].message.content or "").strip()
    usage = getattr(response, "usage", None)
    input_tokens = getattr(usage, "prompt_tokens", 0) or 0
    output_tokens = getattr(usage, "completion_tokens", 0) or 0
    return text, input_tokens, output_tokens


def _yield_text_chunks(text: str, chunk_size: int = 20) -> Generator[str, None, None]:
    for index in range(0, len(text), chunk_size):
        yield f"data: {text[index:index + chunk_size]}\n\n"
    yield "data: [DONE]\n\n"


def call_anthropic_text(
    client: Any,
    model_name: str,
    system_prompt: str,
    user_prompt: str,
    max_tokens: int,
    temperature: Optional[float] = None,
) -> TextCallResult:
    response = client.messages.create(
        **_build_anthropic_request(
            model_name=model_name,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=max_tokens,
            temperature=temperature,
        )
    )
    return _extract_anthropic_result(response)


def call_gemini_text(
    client: Any,
    model_name: str,
    system_prompt: str,
    user_prompt: str,
    temperature: Optional[float] = None,
) -> TextCallResult:
    response = client.models.generate_content(
        model=model_name,
        config=_build_gemini_config(system_prompt=system_prompt, temperature=temperature),
        contents=user_prompt,
    )
    text = getattr(response, "text", "") or ""
    usage = getattr(response, "usage_metadata", None)
    input_tokens = getattr(usage, "prompt_token_count", 0) or 0
    output_tokens = getattr(usage, "candidates_token_count", 0) or 0
    return text, input_tokens, output_tokens


def call_chat_completion_text(
    client: Any,
    model_name: str,
    system_prompt: str,
    user_prompt: str,
    provider_name: str,
    max_tokens: Optional[int] = None,
    reasoning_effort: Optional[str] = None,
) -> TextCallResult:
    request: dict[str, Any] = {
        "model": model_name,
        "messages": _build_chat_messages(system_prompt=system_prompt, user_prompt=user_prompt),
    }
    if max_tokens is not None:
        request["max_tokens"] = max_tokens
    if reasoning_effort is not None:
        request["reasoning_effort"] = reasoning_effort

    response = client.chat.completions.create(**request)
    return _extract_chat_completion_result(response, provider_name)


def call_grok_text(
    client: Any,
    model_name: str,
    system_prompt: str,
    user_prompt: str,
) -> TextCallResult:
    chat_session = client.chat.create(model=model_name)
    chat_session.append(grok_system_message(system_prompt))
    chat_session.append(grok_user_message(user_prompt))
    response = chat_session.sample()
    text = getattr(response, "content", "") or ""
    usage = getattr(response, "usage", None)
    input_tokens = getattr(usage, "prompt_tokens", 0) or 0
    output_tokens = getattr(usage, "completion_tokens", 0) or 0
    return text, input_tokens, output_tokens


def call_openai_text(
    client: Any,
    model_name: str,
    system_prompt: str,
    user_prompt: str,
    max_tokens: int,
) -> TextCallResult:
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
        input_tokens = getattr(usage, "input_tokens", 0) or 0
        output_tokens = getattr(usage, "output_tokens", 0) or 0
        return text, input_tokens, output_tokens

    return call_chat_completion_text(
        client=client,
        model_name=model_name,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        provider_name="GPT-4",
        max_tokens=max_tokens,
    )


def stream_anthropic_text(
    client: Any,
    model_name: str,
    system_prompt: str,
    user_prompt: str,
    max_tokens: int,
) -> Generator[str, None, None]:
    with client.messages.stream(
        **_build_anthropic_request(
            model_name=model_name,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=max_tokens,
        )
    ) as stream:
        for text in stream.text_stream:
            yield f"data: {text}\n\n"
    yield "data: [DONE]\n\n"


def stream_chat_completion_text(
    client: Any,
    model_name: str,
    system_prompt: str,
    user_prompt: str,
    max_tokens: Optional[int] = None,
) -> Generator[str, None, None]:
    request: dict[str, Any] = {
        "model": model_name,
        "messages": _build_chat_messages(system_prompt=system_prompt, user_prompt=user_prompt),
        "stream": True,
    }
    if max_tokens is not None:
        request["max_tokens"] = max_tokens

    stream = client.chat.completions.create(**request)
    for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            yield f"data: {chunk.choices[0].delta.content}\n\n"
    yield "data: [DONE]\n\n"


def stream_gemini_text(
    client: Any,
    model_name: str,
    system_prompt: str,
    user_prompt: str,
) -> Generator[str, None, None]:
    response = client.models.generate_content_stream(
        model=model_name,
        config=_build_gemini_config(system_prompt=system_prompt),
        contents=user_prompt,
    )
    for chunk in response:
        if hasattr(chunk, "text") and chunk.text:
            yield f"data: {chunk.text}\n\n"
    yield "data: [DONE]\n\n"


def stream_grok_text(
    client: Any,
    model_name: str,
    system_prompt: str,
    user_prompt: str,
) -> Generator[str, None, None]:
    chat_session = client.chat.create(model=model_name)
    chat_session.append(grok_system_message(system_prompt))
    chat_session.append(grok_user_message(user_prompt))
    response = chat_session.sample()
    text = getattr(response, "content", "") or ""
    yield from _yield_text_chunks(text)


def stream_openai_text(
    client: Any,
    model_name: str,
    system_prompt: str,
    user_prompt: str,
    max_tokens: int,
) -> Generator[str, None, None]:
    if not model_name.startswith("gpt-5") or "chat" in model_name:
        yield from stream_chat_completion_text(
            client=client,
            model_name=model_name,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=max_tokens,
        )
        return

    response = client.responses.create(
        model=model_name,
        instructions=system_prompt,
        input=user_prompt,
        reasoning={"effort": "medium"},
        text={"verbosity": "medium"},
    )
    text = getattr(response, "output_text", "") or ""
    yield from _yield_text_chunks(text)


__all__ = [
    "call_anthropic_text",
    "call_chat_completion_text",
    "call_gemini_text",
    "call_grok_text",
    "call_openai_text",
    "stream_anthropic_text",
    "stream_chat_completion_text",
    "stream_gemini_text",
    "stream_grok_text",
    "stream_openai_text",
]
