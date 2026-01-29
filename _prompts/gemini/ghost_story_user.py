"""괴담 생성 유저 프롬프트"""


def get_ghost_story_user_prompt(
    keyword: str,
    setting: str = "",
    style: str = "",
) -> str:
    """괴담 유저 프롬프트 생성

    Args:
        keyword: 괴담 주제/키워드 (예: 폐병원, 엘리베이터, 군대)
        setting: 배경 설정 (예: 아파트, 학교, 지하철)
        style: 스타일 (예: 실화풍, 레전드풍, 짧은괴담)
    """

    prompt = f"""
## 키워드
{keyword}

## 배경
{setting if setting else "현대 한국 도시"}

## 스타일
{style if style else "친구한테 들려주는 실화풍"}

## 요청
위 키워드로 소름끼치는 괴담을 작성해줘.
실제로 있었던 일처럼, 친구한테 얘기하듯이 써줘.

제목 없이 본문만 작성해.
"""

    return prompt.strip()
