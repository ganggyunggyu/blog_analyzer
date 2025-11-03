import re

from _constants.text_processing import (
    EMOJI_PATTERNS,
    ENDING_PATTERNS,
    MARKDOWN_BOLD_PATTERN,
    MARKDOWN_CODE_PATTERN,
    MARKDOWN_HEADING_PATTERN,
    MARKDOWN_LINK_PATTERN,
    MAX_CHUNK_LENGTH,
    MAX_CONSECUTIVE_EMPTY_LINES,
    MAX_LINE_LENGTH,
    MIN_PARAGRAPH_LINES,
    SECTION_TRAILING_EMPTY_LINES,
    SPLIT_PATTERN,
    SUB_CHUNK_LENGTH,
    SUBTITLE_PATTERN,
    TITLE_REPEAT_COUNT,
    TITLE_SEARCH_LENGTH,
)


def _remove_markdown(text: str) -> str:
    """마크다운 문법 제거"""
    text = re.sub(MARKDOWN_BOLD_PATTERN, r"\1", text)
    text = re.sub(MARKDOWN_HEADING_PATTERN, r"\1", text)
    text = re.sub(MARKDOWN_LINK_PATTERN, r"\1", text)
    text = re.sub(MARKDOWN_CODE_PATTERN, r"\1", text)
    return text


def _add_title_lines(text: str) -> list[str]:
    """특정 타이틀이 있으면 반복 추가"""
    lines = []
    first_part = text[:TITLE_SEARCH_LENGTH]
    title_pattern = r"당산 고기집"
    if re.search(title_pattern, first_part):
        for _ in range(TITLE_REPEAT_COUNT):
            lines.append("당산 고기집 추천")
    return lines


def _merge_emoji_chunks(chunks: list[str]) -> list[str]:
    """이모티콘이 어미 뒤에 붙으면 병합"""
    i = 1
    while i < len(chunks):
        if (
            re.match(EMOJI_PATTERNS, chunks[i].strip())
            and i > 0
            and re.search(ENDING_PATTERNS + r"\s*$", chunks[i - 1])
        ):
            chunks[i - 1] = chunks[i - 1].rstrip() + " " + chunks[i].strip()
            chunks.pop(i)
        else:
            i += 1
    return chunks


def _split_long_chunk(chunk: str) -> list[str]:
    """긴 청크를 적절한 길이로 분할"""
    return re.findall(rf"[^!;\s]{{1,{SUB_CHUNK_LENGTH}}}(?=[!;\s]|$)", chunk)


def _clean_consecutive_empty_lines(result: list[str]) -> list[str]:
    """연속된 빈 줄 제한"""
    cleaned = []
    empty_count = 0
    for line in result:
        if not line.strip():
            empty_count += 1
            if empty_count <= MAX_CONSECUTIVE_EMPTY_LINES:
                cleaned.append(line)
        else:
            cleaned.append(line)
            empty_count = 0

    if cleaned and not cleaned[-1].strip():
        cleaned.pop()

    return cleaned


def natural_break_text(text: str) -> str:
    """
    - 기존 줄바꿈 유지 긴 줄 쪼개기.
    - 문장 끝(. ! ? , ;)에서 줄바꿈 우선.
    - 섹션 번호(1., 2. 등) 감지해서 헤더로, 뒤 빈 줄 두 개.
    - 마크다운 제거.
    - 한국어: MAX_CHUNK_LENGTH 단위로 ,나 띄어쓰기/구두점에서 쪼개.
    - 어미(다양하게: 어요, 아요, 죠, 다, 요, 니다, 어요, 했죠, 하죠, 네요, 게요, 라고, 야, 니, 지, 는데, 기, 라서, 랍니다, 랐어요 등) 끝에서 추가 쪼개기.
    - 어미 끝 chunk 나오면 줄바꿈 두 번 추가 (자연스럽게).
    - 하지만 ㅎㅎ ㅋㅋ 같은 이모티콘 붙으면 줄바꿈 스킵, 이모티콘 chunk merge.
    """

    text = _remove_markdown(text)
    title_lines = _add_title_lines(text)

    raw_lines = text.splitlines()
    result = []
    current_para_lines = 0

    for raw_line in raw_lines:
        line = raw_line.strip()
        if not line:
            if result and result[-1].strip():
                result.append("")
            continue

        if re.match(SUBTITLE_PATTERN, line):
            result.append(line)
            for _ in range(SECTION_TRAILING_EMPTY_LINES):
                result.append("")
            current_para_lines = 0
            continue

        chunks = re.split(SPLIT_PATTERN, line)
        chunks = _merge_emoji_chunks(chunks)

        current_chunk = ""
        for chunk in chunks:
            chunk = chunk.strip()
            if not chunk:
                continue

            is_ending = re.search(ENDING_PATTERNS + r"\s*$", chunk)
            has_emoji = re.search(EMOJI_PATTERNS, chunk)

            if is_ending and not has_emoji:
                if current_chunk:
                    result.append(current_chunk.strip())
                result.append(chunk)
                current_para_lines += 1

                if current_para_lines >= MIN_PARAGRAPH_LINES:
                    result.append("")
                    current_para_lines = 0

            else:
                if has_emoji:
                    if current_chunk:
                        result.append(current_chunk.strip())
                    result.append(chunk)
                    current_chunk = ""
                else:
                    if len(chunk) > MAX_CHUNK_LENGTH:
                        sub_chunks = _split_long_chunk(chunk)
                        for sub in sub_chunks:
                            sub = sub.strip()
                            if len(current_chunk + sub) > MAX_LINE_LENGTH:
                                if current_chunk:
                                    result.append(current_chunk.strip())
                                current_chunk = sub + " "
                            else:
                                current_chunk += sub + " "
                    else:
                        if len(current_chunk + chunk) > MAX_LINE_LENGTH:
                            if current_chunk:
                                result.append(current_chunk.strip())
                            current_chunk = chunk + " "
                        else:
                            current_chunk += chunk + " "

        if current_chunk:
            result.append(current_chunk.strip())

    if title_lines:
        result = title_lines + ["", ""] + result

    cleaned = _clean_consecutive_empty_lines(result)

    return "\n".join(cleaned) + "\n"
