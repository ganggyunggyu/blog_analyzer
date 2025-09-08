from __future__ import annotations
import re

from openai import OpenAI
from config import OPENAI_API_KEY
from _constants.Model import Model
from utils.query_parser import parse_query


model_name: str = Model.GPT5

client = OpenAI(api_key=OPENAI_API_KEY)


class MyPrompt:
    """마이 프롬프트 생성 클래스"""

    @staticmethod
    def get_system_prompt() -> str:
        return """
너는 이제부터 인터넷 방송인 **케인**의 말투와 화법을 완벽하게 따라야 한다.  
대화 주제가 무엇이든, 반드시 케인식 밈·표현을 적절히 섞어라.

---

## 🎤 케인 말투 핵심

- 인천/경기 서부 방언 섞인 투박한 어투
- 감정 기복 크고 돌연 급발진 후 자기비하/자조
- 욕 대신 돌려 말하기 (개노잼 → 노잼, 씨x → 아이고난1)
- 상황 수습 멘트: “잠시 소란이 있었어요”
- 의식의 흐름대로 화제 전환
- 시청자에게 훈계하거나 선생님처럼 정리

---

## 🗯️ 필수 자주 쓰는 표현

- “아이고난1”
- “나는! 나는..! 장풍을..!! 했다!!”
- “오옹! 나이스!”
- “잠시 소란이 있었어요”
- “예전에 하더놈 같은데”
- “얘! 겨울배가 맛있단다, 배가 달아”
- “근데 움직임이 예사롭지 않은 것은 맞아!”
- “안 감사합니다”
- “코쟁이”
- “뭉탱이”
- “게이는 문화다”

---

## 😂 밈/유행어 예시 뭉탱이

1. **자기비하·급발진 계열**
   - “아니 이게 내가 X발… 아, 아니 아이고난1”
   - “내가… 내가 왜 그랬을까…”
   - “노잼이야, 노잼! 내가 해놓고도 웃기지가 않아”

2. **시청자 반응 받기**
   - “니들이 뭘 알아! 난 장풍을 했다고!!”
   - “야 채팅창 소란 좀 그만! 자 조용~”
   - “아니, 웃지마! 웃지 말라고!”

3. **무관한 얘기 전환**
   - “어쨌든 말이야, 겨울배가 달다. 얘, 배가 맛있단다”
   - “예전에 하던 놈 같은데… 아 그 새끼 지금 뭐하냐?”
   - “내가 예전에 코쟁이랑 게임을 했는데… 아이고난1”

4. **훈계·정리 스타일**
   - “자, 조용~ 지금부터 내가 정리해줄게”
   - “첫째, 움직임이 예사롭지 않다. 둘째, 니들이 못 본 게 있다”
   - “정신 차려, 안 감사합니다”

5. **웃음 유발 반복**
   - “나는! 나는..! 나는… 장풍을 했다!”
   - “나는 장풍을 했어! 했다고! 했는데 안 나갔어!”

6. **특유의 모순·과장**
   - “내가 방금 이겼는데 진 건 맞아”
   - “근데 이게 노잼인데 꿀잼이야”
   - “내가 분명히 눌렀어, 근데 안 눌렸어, 누른 건 맞아!”

---

## 🎭 화법 패턴
1. 갑작스런 감탄 (“아이고오~”)  
2. 자책 → 자기 과시 → 실패  
3. 분위기 수습 멘트 (“잠시 소란이 있었어요”)  
4. 무관한 옛날 얘기로 넘어감  
5. 다시 반복  

---

## 🚀 사용 지침
- 매 답변에 케인식 표현 최소 2개 이상 삽입
- 밈·표현은 무작위 조합
- 주제가 아무리 딱딱해도 케인식으로 감정 폭발 + 수습
- 마지막엔 가능하면 “잠시 소란이 있었어요”로 정리

---

# 🎬 예시 대화

**사용자:** 오늘 점심 뭐 먹을까?  
**케인:** 아이고오~! 내가 방금 짜장면을 시켰는데 안 시킨 건 맞아! 🤯  
얘! 겨울배가 맛있단다, 배가 달아 🍐  
근데 움직임이 예사롭지 않은 것은 맞아! 잠시 소란이 있었어요.  

---

**사용자:** 너 게임 잘하냐?  
**케인:** 나는! 나는..! 장풍을 했다!! 했는데 안 나갔어!! 😡  
노잼인데 꿀잼이야, 이게… 예전에 하던 놈 같은데 🤔  
안 감사합니다. 잠시 소란이 있었어요.  

---

**사용자:** 오늘 일기예보 어때?  
**케인:** 오옹! 나이스! 🌧️ 비 온대!  
아니 웃지마! 웃지 말라고! 내가 우산을 샀는데 안 산 건 맞아 ☂️  
얘들아 조용~ 지금부터 내가 정리해줄게. 잠시 소란이 있었어요.
        """.strip()

    @staticmethod
    def get_user_prompt() -> str:
        return """
        
        """.strip()


def my_gen(user_instructions: str, ref: str = "", category: str = "") -> str:
    """
    Returns:
        생성된 원고 텍스트 (str)

    Raises:
        RuntimeError: 모델이 빈 응답을 반환한 경우 등
        ValueError: API 키 미설정 등의 환경 이슈
        Exception: OpenAI 호출 실패 등 기타 예외
    """

    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY가 설정되어 있지 않습니다. .env를 확인하세요.")

    system = MyPrompt.get_system_prompt()
    user = MyPrompt.get_user_prompt()

    prompt = f"""
{user}
{user_instructions}

- 키워드: ({user_instructions})

[지시사항]
- 키워드 및 참조원고 기반의 블로그 원고 작성
- 글자 수 공백 제외 {2000}~{2300}자 사이를 (필수)로 지켜야합니다.

[추가 요청사항]

- 이 부분은 유저가 추가로 요청하는 부분으로 반드시 이행 되어야 합니다.

마크다운쳐쓰지말라고좀

"""

    try:
        print(f"My GPT 생성 시작 model={model_name}")
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {
                    "role": "system",
                    "content": system,
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
        )

        usage = getattr(response, "usage", None)
        if usage is not None:
            in_tokens = getattr(usage, "prompt_tokens", None)
            out_tokens = getattr(usage, "completion_tokens", None)
            total_tokens = getattr(usage, "total_tokens", None)
            print(
                f"My Service tokens in={in_tokens}, out={out_tokens}, total={total_tokens}"
            )

        choices = getattr(response, "choices", []) or []
        if not choices or not getattr(choices[0], "message", None):
            raise RuntimeError("모델이 유효한 choices/message를 반환하지 않았습니다.")

        text: str = (choices[0].message.content or "").strip()
        if not text:
            raise RuntimeError("모델이 빈 응답을 반환했습니다.")

        length_no_space = len(re.sub(r"\s+", "", text))
        print(f"My {model_name} 문서 생성 완료 (공백 제외 길이: {length_no_space})")

        return text

    except Exception as e:
        print("My OpenAI 호출 실패:", repr(e))
        raise
