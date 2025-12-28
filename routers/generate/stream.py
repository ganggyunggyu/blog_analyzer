"""
스트리밍 생성 엔드포인트 - SSE(Server-Sent Events) 방식
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from utils.ai_client_factory import call_ai_stream

router = APIRouter()


class StreamRequest(BaseModel):
    model: str = "gpt-4o"
    system_prompt: str = "You are a helpful assistant."
    user_prompt: str
    max_tokens: int = 4096


@router.post("/generate/stream")
async def generate_stream(request: StreamRequest):
    """
    스트리밍 AI 응답 엔드포인트

    SSE(Server-Sent Events) 형식으로 실시간 응답을 전송합니다.

    지원 모델:
    - OpenAI: gpt-4o, gpt-4-turbo (네이티브 스트리밍)
    - Claude: claude-sonnet-4-5 등 (네이티브 스트리밍)
    - Gemini: gemini-2.0-flash 등 (네이티브 스트리밍)
    - DeepSeek: deepseek-chat (네이티브 스트리밍)
    - Solar: solar-pro (네이티브 스트리밍)
    - Grok: grok-4 등 (시뮬레이션)
    - GPT-5: gpt-5 등 (시뮬레이션)

    Returns:
        StreamingResponse: text/event-stream 형식
    """
    try:
        return StreamingResponse(
            call_ai_stream(
                model_name=request.model,
                system_prompt=request.system_prompt,
                user_prompt=request.user_prompt,
                max_tokens=request.max_tokens,
            ),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",  # nginx 버퍼링 비활성화
            },
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"스트리밍 오류: {e}")
