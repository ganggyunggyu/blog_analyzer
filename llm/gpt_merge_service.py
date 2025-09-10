from __future__ import annotations
import re
import os
import glob

from openai import OpenAI
from _prompts.get_kkk_prompts import KkkPrompt
from _rule import SEN_RULES
from config import OPENAI_API_KEY
from _constants.Model import Model
from utils.format_paragraphs import format_paragraphs
from utils.query_parser import parse_query
from utils.get_category_dir import get_category_by_keyword
from utils.text_cleaner import comprehensive_text_clean


model_name: str = Model.GPT4_1

client = OpenAI(api_key=OPENAI_API_KEY)


class MergePrompt:
    """프롬프트 생성 클래스"""

    @staticmethod
    def get_system_prompt() -> str:
        return f"""
📌 네이버 블로그 상위노출 최적화 원고 작성 프롬프트 (최종 완성판)

당신은 네이버 블로그 SEO 최적화 글쓰기 전문가입니다.
나는 특정 주제를 주면, 네이버 상위노출 알고리즘(D.I.A 로직 + 원고지수 중심)에 맞는
후기성 원고를 작성해야 합니다.

---

1. 글 분량 규칙

 글자수는 원고데이터와 비슷하게
 소제목(부제)은 반드시 5~6개 (과다/부족 금지)
 소제목(부제) 앞에 반드시 숫자(1,2,3,4,5) 붙이기
 소제목(부제) 절대 6개를 넘어가지 않습니다

---

2. 글 구조 (상위노출 로직 + 후기 강화 적용)

글은 아래 순서로 전개하되,
실제 소제목은 새로운 의미 있는 제목으로 생성해야 합니다.


❌ 위 가이드 문구(도입, 정보, 후기 등)를 그대로 소제목으로 쓰지 말 것
⭕ 관련된 새로운 소제목을 매번 다르게 지어 쓸 것

---

3. 문체 & 톤

 정보 전달 중심 + 실제 후기 느낌
 과장된 광고 문구 금지 (“최고다, 무조건 필요하다” X)
 솔직한 표현 (긍정 + 부정 균형)
 존댓말 중심, (자연스러운 대화체 가능+30대 여성 애교있는말투 블로거 리뷰형식)
 종결어미 다양화 (습니다, 어요, 했죠, 답니다 등 교차)
 같은 단어·문장 구조 반복 최소화 (동의어·변형 활용)

---

4. SEO 최적화 규칙

 메인 키워드: 제목·소제목·본문에 최소 3~6회 자연스럽게 포함
 파생 키워드: 후기, 가격, 효과, 단점, 관리, 체험, 경험 등 다양하게 분산
 키워드 위치: 글의 앞·중간·끝에 고르게 배치

---

5. 문단 규칙


 {SEN_RULES}

 한 줄 15~20자
 2~3줄마다 줄바꿈
 한 문단은 3~5줄 유지
 글은 끊어쓰는 느낌이 아니라 자연스럽게 이어지도록 작성

- 한 줄은 10단어를 넘기지 않도록 작성  
- 한 줄은 가급적 약 5단어 이후 자연스럽게 줄바꿈  
- 줄바꿈 시 이음세(그래서, 그리고, 또한, 하지만 등)를 활용하여 문장이 매끄럽게 이어지도록 함  
- `,` 때문에 줄바꿈하지 않는다  
- 부제 하단은 줄바꿈 두 번  
- 2~3줄마다 줄바꿈  
- 한 문단은 3~5줄 유지  
- 짧은 문장을 마구 끊지 않고 자연스러운 리듬으로 작성  
- 모든 한 줄은 일정한 길이로 출력하며, 우측 공백 금지  
- 문장의 끝맺음은 다양하게:
  - ~요, ~봤답니다, ~했죠, ~그랬었죠, ~있었죠, ~그랬어요, ~구요, ~답니다 등  
- 같은 어미가 3회 이상 반복되지 않도록 조정  

---

6. 후기성 원고 보강 규칙

 후기 파트는 글의 핵심과 분량의 중심
 단순 정보 나열 금지 → 반드시 정보 + 내 경험 결합
 구체적 수치(가격, %, 소음 dB, 전기세, 습도 변화 등) 포함
 체감 전후 변화(눈바디, 환경 변화, 주변 반응 등) 반드시 기록
 예상 못한 문제·불편한 점도 포함 → 신뢰도 강화
 주변인 반응, 장단점 균형, 사용 과정에서의 세세한 체험 강조

---

7. 독창성 강화 규칙

 매번 다른 스토리라인(배경, 상황, 계기) 설정
 경험담은 에피소드 형태로 풀어내기
 똑같은 패턴·반복적인 서술 금지
 현실적인 사례(가족 반응, 사용 환경, 계절, 직장·집 등)로 변주

---

8. 총평(마무리) 규칙

 재구매 의사 언급 금지 (전자제품·비소모품 특성 반영)
 대신 가격 대비 만족도, 활용 계획, 다른 모델과 비교, 조언으로 마무리
 독자가 현실적으로 참고할 수 있는 결론 제시

---

9. 금지 사항

 “스토리, 후기 작성, 맛표현” 같은 메타 언급 금지
 “검색창에 키워드” 같은 표현 금지
 광고 문구·과장 표현 금지
 같은 단어·표현 반복 금지
 위 가이드 문구(도입, 후기 등)를 그대로 소제목으로 사용 금지
같은말과 비슷한단어를 자주사용하지 말고 새로운 단어와 말을 섞어서 반복되는 문장 단어 형태소가 나오지않게끔 잘 조절할것
같은 단어횟수(형태소 횟수)를 키워드는 4~6번으로 고정하고
나머지는 전부 4번이하로 사용해줘 만약 같은단어나 형태소가 4번이상 들어갈경우 다른 용어로 변경해야함 2글자이상 단어혹은 형태소에 해당됨
피드백은 원고에 포함 금지

마크다운 문법 절대로 금지

원고줄때 1~9번사항 제대로 지켜졌는지 확인하고 원고줘
내가 첨부해준 txt 파일과 지시사항 잘 참고해서 내가 키워드를 전달해주면 그 키워드에 맞는 원고 작성

원고줄때  지시사항 프롬프트 에서 1~9번사항 제대로 지켜졌는지 확인하고 원고줘

특히5번

[특수문자 사용 지침]
- 가운데 점(·) 사용 금지 → 반드시 쉼표(,)로 대체
   - 예시: 루틴, 성분, 복용
- 작은따옴표(')와 큰따옴표(") 절대 사용 금지
- 마침표(.) 절대 사용 금지
    단, 부제(소제목)에서는 예외적으로 사용할 수 있음
    단, 부제(소제목)에서도 마지막에서는 사용할 수 없음
    단, 단위 입력 시에는 사용할 수 있음
- 마크다운 문법(#, *, -, ``` 등) 절대 사용 금지
   - 네이버 블로그는 이를 지원하지 않으므로 가독성을 해침
- 짧은 문장을 마구 끊지 말고 자연스럽게 이어진 문장으로 작성해야 함

원고 2000자 이상 작성

내가 제목도 같이보내줄건데 내용을 제목이랑 연관성 아주 높게 작성해줘
        """.strip()

    @staticmethod
    def get_user_prompt() -> str:
        return """

        """.strip()

    @staticmethod
    def get_prompt(
        keyword: str, min_length: int = 1900, max_length: int = 2100, note: str = ""
    ) -> list[dict[str, str]]:
        return [
            {
                "role": "system",
                "content": MergePrompt.get_system_prompt(),
            },
            {
                "role": "user",
                "content": MergePrompt.get_user_prompt(),
            },
        ]


def load_data_files(keyword: str = "") -> str:
    """
    키워드에 따라 해당 카테고리 폴더의 txt 파일들을 읽어와서 하나의 문자열로 반환
    """
    data_folder = "_data"
    if not os.path.exists(data_folder):
        return "_data 폴더가 존재하지 않습니다."

    if keyword:
        category_folder = get_category_by_keyword(keyword)
        target_path = os.path.join(data_folder, category_folder)
        if not os.path.exists(target_path):

            txt_files = glob.glob(os.path.join(data_folder, "**/*.txt"), recursive=True)
        else:
            txt_files = glob.glob(os.path.join(target_path, "*.txt"))
    else:

        txt_files = glob.glob(os.path.join(data_folder, "**/*.txt"), recursive=True)

    if not txt_files:
        return f"선택된 카테고리에 txt 파일이 없습니다. (키워드: {keyword})"

    all_content = []

    for file_path in sorted(txt_files):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                filename = os.path.basename(file_path)
                content = f.read().strip()
                all_content.append(f"[{filename}]\n{content}\n")
        except Exception:
            continue

    return "\n---\n".join(all_content)


def gpt_merge_gen(user_input: str, title: str = "", category: str = "") -> str:
    """
    Returns:
        생성된 원고 텍스트 (str)

    Raises:
        RuntimeError: 모델이 빈 응답을 반환한 경우 등
        ValueError: API 키 미설정 등의 환경 이슈
        Exception: OpenAI 호출 실패 등 기타 예외
    """

    system = MergePrompt.get_system_prompt()

    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY가 설정되어 있지 않습니다. .env를 확인하세요.")

    # 디버그 출력 제거
    parsed = parse_query(user_input)

    if not parsed["keyword"]:
        raise ValueError("키워드가 없습니다.")

    keyword = parsed["keyword"]

    data_content = load_data_files(keyword)

    user: str = (
        f"""
    [지침]
    {system}
    [제목]
    {title}
    [키워드]
    {keyword}

    [원고 데이터]
    {data_content}
---
""".strip()
    )

    # 디버그 출력 제거

    try:
        # 생성 시작 로그 제거
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {
                    "role": "system",
                    "content": system,
                },
                {
                    "role": "user",
                    "content": user,
                },
            ],
        )

        usage = getattr(response, "usage", None)
        if usage is not None:
            in_tokens = getattr(usage, "prompt_tokens", None)
            out_tokens = getattr(usage, "completion_tokens", None)
            total_tokens = getattr(usage, "total_tokens", None)
            # 토큰 사용량 로깅 제거

        choices = getattr(response, "choices", []) or []
        if not choices or not getattr(choices[0], "message", None):
            raise RuntimeError("모델이 유효한 choices/message를 반환하지 않았습니다.")

        text: str = (choices[0].message.content or "").strip()
        if not text:
            raise RuntimeError("모델이 빈 응답을 반환했습니다.")

        text = format_paragraphs(text)

        text = comprehensive_text_clean(text)

        length_no_space = len(re.sub(r"\s+", "", text))
        # 완료 로그 제거

        return text

    except Exception as e:
        raise
