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

    elif ai_service_type == "claude":
        response = client.messages.create(
            model=model_name,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
            max_tokens=max_tokens,
        )
        content_blocks = getattr(response, "content", [])
        text = getattr(content_blocks[0], "text", "") if content_blocks else ""

    elif ai_service_type == "openai":
        if model_name.startswith("gpt-4"):
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
        else:
            # GPT-5 시리즈: Responses API
            response = client.responses.create(
                model=model_name,
                instructions=system_prompt,
                input=user_prompt,
                reasoning={"effort": "medium"},
                text={"verbosity": "medium"},
            )
            text = getattr(response, "output_text", "") or ""

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

    elif ai_service_type == "grok":
        chat_session = client.chat.create(model=model_name)
        chat_session.append(grok_system_message(system_prompt))
        chat_session.append(grok_user_message(user_prompt))
        response = chat_session.sample()
        text = getattr(response, "content", "") or ""

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

    else:
        raise ValueError(f"지원하지 않는 AI 서비스 타입: {ai_service_type}")

    text = text.strip()
    if not text:
        raise RuntimeError("빈 응답을 받았습니다.")

    return text
