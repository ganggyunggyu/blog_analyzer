import anthropic
import os
from _prompts.get_claude_prompts import ClaudePrompt
from config import CLAUDE_API_KEY
from llm.claude_file_uploader import get_file_ids
from enum import Enum


class ClaudeModel(Enum):
    OPUS_4_1 = "claude-opus-4-1-20250805"
    OPUS_4_0 = "claude-opus-4-20250514"
    SONNET_4 = "claude-sonnet-4-20250514"
    SONNET_3_7 = "claude-3-7-sonnet-20250219"
    HAIKU_3_5 = "claude-3-5-haiku-20241022"


def claude_gen(keyword: str, ref: str = "") -> str:

    user = ClaudePrompt.get_user_prompt()
    system = ClaudePrompt.get_system_prompt()
    model = ClaudeModel.HAIKU_3_5.value

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

    print(document_blocks)

    user = f"""
[키워드]
{keyword}

[제목]
{ref}
"""

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
                        "text": user,
                    },
                    *document_blocks,
                ],
            }
        ],
        extra_headers={"anthropic-beta": "files-api-2025-04-14"},
    )

    text_parts = []
    for block in response.content:
        if block.type == "text":
            text_parts.append(block.text)

    return "".join(text_parts).strip()
