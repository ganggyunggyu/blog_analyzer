import anthropic
import os
from _prompts.get_claude_prompts import ClaudePrompt
from config import CLAUDE_API_KEY
from enum import Enum


def file_upload(file_name):
    client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)
    client.beta.files.upload(
        file=(
            f"{file_name}.txt",
            open(
                f"/Users/ganggyunggyu/Programing/21lab/blog_analyzer/_docs/claude_docs/{file_name}.txt",
                "rb",
            ),
            "text/plain",
        ),
    )


def get_file_list():
    import anthropic

    client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)
    files = client.beta.files.list()
    print(files)
    return files


def get_file_ids():
    import anthropic

    client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)
    all_ids = []
    starting_after = None

    while True:
        response = client.beta.files.list(
            limit=1,
        )
        files = response.data

        if not files:
            break

        all_ids.extend([f.id for f in files])
        starting_after = files[-1].id  # 다음 페이지로 이동

        if not response.has_more:  # 더 이상 없으면 중단
            break

    return all_ids


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
    model = ClaudeModel.SONNET_4.value

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

[키워드]
{keyword}

[제목]
{ref}
"""

    try:
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
                            "text": "문서들 분석해줘",
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

    except (BadRequestError, RateLimitError) as e:
        if hasattr(e, "body") and isinstance(e.body, dict):
            print(e.body)
            usage = e.body.get("usage", {})
            input_tokens = usage.get("input_tokens")
            output_tokens = usage.get("output_tokens")
            total = usage.get("total_tokens")

            print("❌ Claude 호출 실패: 토큰 초과 또는 오류 발생")
            print(f"입력 토큰 수: {input_tokens}")
            print(f"출력 토큰 수: {output_tokens}")
            print(f"총합 토큰 수: {total}")

        raise e  # 필요 시 에러 다시 raise
