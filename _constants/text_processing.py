"""텍스트 처리 관련 상수 정의"""

# 청크 및 라인 길이 제한
MAX_CHUNK_LENGTH = 35
MAX_LINE_LENGTH = 30
SUB_CHUNK_LENGTH = 28

# 단락 구조 관련
MIN_PARAGRAPH_LINES = 2
MAX_CONSECUTIVE_EMPTY_LINES = 2
SECTION_TRAILING_EMPTY_LINES = 2

# 특정 타이틀 반복 설정
TITLE_SEARCH_LENGTH = 300
TITLE_REPEAT_COUNT = 4

# 정규식 패턴: 한국어 문장 종결 어미
ENDING_PATTERNS = r"(어요|아요|니다|습니다|했어요|했죠|하죠|네요|게요|랍니다|랐어요|했습니다|합니다|거예요|고요|구요|져요|인데|요.|다.|죠.)"

# 정규식 패턴: 이모티콘
EMOJI_PATTERNS = r"^[ㅎㅋㅠ\s]{1,3}$"

# 정규식 패턴: 섹션 번호 (1., 2. 등)
SUBTITLE_PATTERN = r"^\d+\.\s+"

# 정규식 패턴: 마크다운 제거용
MARKDOWN_BOLD_PATTERN = r"\*\*(.*?)\*\*"
MARKDOWN_HEADING_PATTERN = r"#{1,6}\s*(.*?)(?=\n|$)"
MARKDOWN_LINK_PATTERN = r"\[([^\]]+)\]\([^\)]+\)"
MARKDOWN_CODE_PATTERN = r"`([^`]+)`"

# 문장 분리 패턴 (한국어 어미 기반)
KOREAN_ENDINGS_FOR_SPLIT = [
    "어요", "아요", "니다", "습니다", "했어요", "했죠", "하죠",
    "네요", "게요", "라고", "라서", "랍니다", "랐어요", "했습니다",
    "합니다", "거예요", "고요", "구요", "져요"
]


def build_split_pattern():
    """한국어 어미 기반 문장 분리 패턴 생성"""
    patterns = [r"(?<=[!;])\s*"]

    for ending in KOREAN_ENDINGS_FOR_SPLIT:
        patterns.append(f"(?<={ending})\\s*(?=\\s)")

    return "|".join(patterns)


SPLIT_PATTERN = build_split_pattern()
