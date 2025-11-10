from _prompts.rules.line_break_rules import line_break_rules
from _constants.Model import Model
from utils.ai_client_factory import call_ai


def apply_line_break(text: str, model_name: str = Model.GROK_4_RES) -> str:
    """
    줄바꿈 규칙을 적용하여 텍스트를 재처리하는 함수

    Args:
        text: 원본 텍스트
        model_name: 사용할 AI 모델 (기본값: Model.GPT5)

    Returns:
        줄바꿈 규칙이 적용된 텍스트

    Raises:
        ValueError: 입력 텍스트가 비어있는 경우
        RuntimeError: AI로부터 빈 응답을 받은 경우
    """
    if not text or not text.strip():
        raise ValueError("입력 텍스트가 비어있습니다.")

    system_prompt = f"""
당신은 블로그 원고의 줄바꿈을 최적화하는 전문가입니다.
아래 줄바꿈 규칙을 정확히 따라 텍스트를 재구성하세요.

{line_break_rules}

# 중요 지침

## 이행 사항
- 한 줄당 30~35자로 제한하세요. 자연스러움에 따라 조정 가능.
- 2~4번째 문장마다 {{두 줄 줄바꿈}}을 적용하세요
- 소제목 하단 {{두 줄 줄바꿈}}
- 마침표 및 쉼표 제거
- 제목 4개 반복 구간, 소제목, 본문의 내용은 그대로 유지하세요
- 만약 원고의 흐름에 맞지 않는 영문 표현 또는 일본어 표현 또는 한자 표현이 있다면 한국어로 수정합니다.
- 문장의 자연스러움이 최우선 되어야 합니다

## 금지 사항
- 마침표 및 쉼표 제거를 제외한 원본 텍스트의 내용 변경
- 제목 내에서의 줄바꿈
- 소제목 내에서의 줄바꿈
- 너무 짧은 문장의 줄바꿈
- 문장이 어색해질 정도로 과한 줄바꿈
- (공백) 문구 삽입 금지

## 길이 초과 허용되는 문장
- (공백)은 예시일 뿐 실제 원고에 추가하지 말것
- 있다면 제거 필수
예:
위치: 서울시 강남구 강남대로96길 22, 2층 (공백)
영업시간: 평일 11:30 - 21:15 (브레이크 타임 14:30 - 15:15, 런치 라스트오더 14:30, 디너 라스트오더 20:30) (공백)
주말 및 공휴일: 11:30 - 21:15 (노 브레이크, 라스트오더 20:30)

## 출력 형식
어떠한 메타 설명이나 추가 텍스트 없이 재구성된 원고만 출력하세요
""".strip()

    user_prompt = f"""
아래 텍스트에 줄바꿈 규칙을 적용해주세요:

{text}
""".strip()

    result_text = call_ai(
        model_name=model_name,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
    )

    return result_text
