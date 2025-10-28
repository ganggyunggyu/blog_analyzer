import re


MAX_CHUNK_LENGTH = 20
MAX_LINE_LENGTH = 15

ENDING_PATTERNS = r"(어요|아요|니다|습니다|했어요|했죠|하죠|네요|게요|랍니다|랐어요|했습니다|합니다|거예요|면서|고요|구요|져요|인데|는데)"

EMOJI_PATTERNS = r"^[ㅎㅋㅠ\s]{1,3}$"


def natural_break_text(text):
    """
    - 기존 줄바꿈 유지하면서 긴 줄 쪼개기.
    - 문장 끝(. ! ? , ;)에서 줄바꿈 우선.
    - 섹션 번호(1., 2. 등) 감지해서 헤더로, 뒤 빈 줄 두 개.
    - 마크다운 제거.
    - 한국어: MAX_CHUNK_LENGTH 단위로 ,나 띄어쓰기/구두점에서 쪼개.
    - 어미(다양하게: 어요, 아요, 죠, 다, 요, 니다, 어요, 했죠, 하죠, 네요, 게요, 라고, 야, 니, 지, 는데, 기, 라서, 랍니다, 랐어요 등) 끝에서 추가 쪼개기.
    - 어미 끝 chunk 나오면 줄바꿈 두 번 추가 (자연스럽게).
    - 하지만 ㅎㅎ ㅋㅋ 같은 이모티콘 붙으면 줄바꿈 스킵, 이모티콘 chunk merge.
    """

    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    text = re.sub(r"#{1,6}\s*(.*?)(?=\n|$)", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)
    text = re.sub(r"`([^`]+)`", r"\1", text)

    lines = []
    first_part = text[:300]
    title_pattern = r"당산 고기집"
    if re.search(title_pattern, first_part):
        for _ in range(4):
            lines.append("당산 고기집 추천")

    raw_lines = text.splitlines()
    result = []

    for raw_line in raw_lines:
        line = raw_line.strip()
        if not line:
            if result and result[-1].strip():
                result.append("")
            continue

        if re.match(r"^\d+\.\s+", line):
            result.append(line)
            result.append("")
            continue

        split_pattern = r"(?<=[.?!;])\s*|(?<=어요)\s*(?=\s)|(?<=아요)\s*(?=\s)|(?<=니다)\s*(?=\s)|(?<=습니다)\s*(?=\s)|(?<=했어요)\s*(?=\s)|(?<=했죠)\s*(?=\s)|(?<=하죠)\s*(?=\s)|(?<=네요)\s*(?=\s)|(?<=게요)\s*(?=\s)|(?<=라고)\s*(?=\s)|(?<=라서)\s*(?=\s)|(?<=랍니다)\s*(?=\s)|(?<=랐어요)\s*(?=\s)|(?<=했습니다)\s*(?=\s)|(?<=합니다)\s*(?=\s)|(?<=거예요)\s*(?=\s)|(?<=면서)\s*(?=\s)|(?<=고요)\s*(?=\s)|(?<=구요)\s*(?=\s)|(?<=져요)\s*(?=\s)|(?<=인데)\s*(?=\s)"
        chunks = re.split(split_pattern, line)

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
        current_chunk = ""
        for chunk in chunks:
            chunk = chunk.strip()
            if not chunk:
                continue

            is_ending = re.search(ENDING_PATTERNS + r"\s*$", chunk)
            has_emoji = re.search(EMOJI_PATTERNS, chunk)
            # has_number = re.search(NUMBER_PATTERNS, chunk)
            if is_ending and not has_emoji:
                if current_chunk:
                    result.append(current_chunk.strip())
                result.append(chunk)
                result.append("")
                current_chunk = ""
            else:
                if has_emoji:
                    if current_chunk:
                        result.append(current_chunk.strip())
                    result.append(chunk)
                    current_chunk = ""
                else:

                    if len(chunk) > MAX_CHUNK_LENGTH:
                        sub_chunks = re.findall(
                            r"[^.?!,;\s]{1,28}(?=[.?!,;\s]|$)", chunk
                        )
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

    if lines:
        result = lines + ["", ""] + result

    cleaned = []
    empty_count = 0
    for r in result:
        if not r.strip():
            empty_count += 1
            if empty_count <= 2:
                cleaned.append(r)
        else:
            cleaned.append(r)
            empty_count = 0

    if cleaned and not cleaned[-1].strip():
        cleaned.pop()

    return "\n".join(cleaned) + "\n"
