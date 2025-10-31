import re


MAX_CHUNK_LENGTH = 35
MAX_LINE_LENGTH = 30

ENDING_PATTERNS = r"(어요|아요|니다|습니다|했어요|했죠|하죠|네요|게요|랍니다|랐어요|했습니다|합니다|거예요|고요|구요|져요|인데|요.|다.|죠.)"

EMOJI_PATTERNS = r"^[ㅎㅋㅠ\s]{1,3}$"
SUBTITLE_PATTERN = r"^\d+\.\s+"


def natural_break_text(text):
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
    # NEW: 현재 단락 라인 수를 추적
    current_para_lines = 0
    for raw_line in raw_lines:
        line = raw_line.strip()
        if not line:
            if result and result[-1].strip():
                result.append("")
            continue

        if re.match(SUBTITLE_PATTERN, line):
            result.append(line)
            result.append("")
            result.append("")
            current_para_lines = 0  # NEW: 섹션 시작이므로 단락 카운터 초기화
            continue

        split_pattern = r"(?<=[!;])\s*|(?<=어요)\s*(?=\s)|(?<=아요)\s*(?=\s)|(?<=니다)\s*(?=\s)|(?<=습니다)\s*(?=\s)|(?<=했어요)\s*(?=\s)|(?<=했죠)\s*(?=\s)|(?<=하죠)\s*(?=\s)|(?<=네요)\s*(?=\s)|(?<=게요)\s*(?=\s)|(?<=라고)\s*(?=\s)|(?<=라서)\s*(?=\s)|(?<=랍니다)\s*(?=\s)|(?<=랐어요)\s*(?=\s)|(?<=했습니다)\s*(?=\s)|(?<=합니다)\s*(?=\s)|(?<=거예요)\s*(?=\s)|(?<=고요)\s*(?=\s)|(?<=구요)\s*(?=\s)|(?<=져요)\s*(?=\s)"
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
                current_para_lines += 1  # NEW

                # ★ NEW: 단락 종료 조건 — 부제 제외, 최소 2줄 보장
                # 직전이 부제가 아니고, 현재 단락이 1줄뿐이면 종료를 보류
                # (= 빈 줄을 넣지 않고 다음 문장을 같은 단락으로 이어감)
                if current_para_lines >= 2:
                    result.append("")  # 단락 종료
                    current_para_lines = 0
                # else: 종료 보류 → 다음 문장과 같은 단락으로 이어짐

            else:
                if has_emoji:
                    if current_chunk:
                        result.append(current_chunk.strip())
                    result.append(chunk)
                    current_chunk = ""
                else:

                    if len(chunk) > MAX_CHUNK_LENGTH:
                        sub_chunks = re.findall(r"[^!;\s]{1,28}(?=[!;\s]|$)", chunk)
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
