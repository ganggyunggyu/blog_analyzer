import anthropic
import time
import os
import re
from llm._claude_file_uploader import get_file_ids
from _prompts.get_claude_prompts import ClaudePrompt
from config import CLAUDE_API_KEY
from enum import Enum


class ClaudeModel(Enum):
    OPUS_4_1 = "claude-opus-4-1-20250805"
    OPUS_4_0 = "claude-opus-4-20250514"
    SONNET_4 = "claude-sonnet-4-20250514"
    SONNET_3_7 = "claude-3-7-sonnet-20250219"
    HAIKU_3_5 = "claude-3-5-haiku-20241022"


from anthropic._exceptions import BadRequestError, RateLimitError


def claude_gen(keyword: str, ref: str = "") -> str:
    user = ClaudePrompt.get_user_prompt()
    system = ClaudePrompt.get_system_prompt()
    model = ClaudeModel.SONNET_3_7.value

    client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)
    file_ids = get_file_ids()

    document_blocks = [
        {
            "type": "document",
            "source": {
                "type": "file",
                "file_id": fid,
            },
        }
        for fid in file_ids
    ]

    prompt = f"""
[지침]
{user}

[키워드]
{keyword}

[제목]
{ref}
"""

    try:
        start_ts = time.time()
        print("원고작성 시작")
        response = client.beta.messages.create(
            model=model,
            max_tokens=4000,
            system=system,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt,
                        },
                        *document_blocks,
                    ],
                }
            ],
            extra_headers={"anthropic-beta": "files-api-2025-04-14"},
        )
        # 디버그 출력 제거

        text_parts = []
        for block in response.content:
            if block.type == "text":
                text_parts.append(block.text)

        text = "".join(text_parts).strip()
        length_no_space = len(re.sub(r"\s+", "", text))
        elapsed = time.time() - start_ts
        print(f"원고 길이 체크: {length_no_space}")
        print(f"원고 소요시간: {elapsed:.2f}s")
        print("원고작성 완료")
        return text

    except (BadRequestError, RateLimitError) as e:
        if hasattr(e, "body") and isinstance(e.body, dict):
            # 오류 상세 출력 제거
            usage = e.body.get("usage", {})
            input_tokens = usage.get("input_tokens")
            output_tokens = usage.get("output_tokens")
            total = usage.get("total_tokens")

            # 토큰 사용량 출력 제거

        raise e  # 필요 시 에러 다시 raise
