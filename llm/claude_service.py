from __future__ import annotations
import re
import time

from anthropic import Anthropic
from anthropic._exceptions import BadRequestError, RateLimitError
from _prompts.service.get_mongo_prompt import get_mongo_prompt
from _prompts.system.ver1 import V1
from config import CLAUDE_API_KEY
from _constants.Model import Model
from utils.query_parser import parse_query
from utils.text_cleaner import comprehensive_text_clean


model_name: str = Model.CLAUDE_OPUS_4_5


def claude_gen(user_instructions: str, ref: str = "", category: str = "") -> str:
    if not CLAUDE_API_KEY:
        raise ValueError(
            "ANTHROPIC_API_KEY가 설정되어 있지 않습니다. .env를 확인하세요."
        )

    parsed = parse_query(user_instructions)
    keyword, note = parsed.get("keyword", ""), parsed.get("note", "")

    if not keyword:
        raise ValueError("키워드가 없습니다.")

    target_chars_min, target_chars_max = 1800, 2000

    mongo_data = get_mongo_prompt(category, user_instructions)

    system = f"""
# 원고 작성 지침
{V1}

# 참고할 데이터
{mongo_data}

# 금지사항
- 마크다운 문법 금지

# 줄바꿈 지침
- 25~30자에 한번 줄바꿈 필수

# 글자수
- 한국어 공백 제거 기준 1800~2300

"""

    user = f"""
    키워드: {keyword}

    추가 요청: {note}

    참조 원고: {ref}
    """

    claude_client = Anthropic(api_key=CLAUDE_API_KEY)

    try:
        start_ts = time.time()
        print(f"서비스: {category}")
        print(f"키워드: {keyword}")
        print("원고작성 시작")

        response = claude_client.messages.create(
            model=model_name,
            system=system,
            messages=[{"role": "user", "content": user}],
            max_tokens=4096,
        )

        content_blocks = getattr(response, "content", [])
        text: str = getattr(content_blocks[0], "text", "") if content_blocks else ""

        text = comprehensive_text_clean(text)

        length_no_space = len(re.sub(r"\s+", "", text))
        elapsed = time.time() - start_ts

        print(f"원고 길이 체크: {length_no_space}")
        print(f"원고 소요시간: {elapsed:.2f}s")
        print("원고작성 완료")

        return text

    except (BadRequestError, RateLimitError) as e:
        print(f"Claude API 오류: {e}")
        raise e
