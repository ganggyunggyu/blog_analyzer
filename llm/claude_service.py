import json
import anthropic
from config import CLAUDE_API_KEY
from prompts.get_ko_prompt import getKoPrompt
from utils.text_len import length_no_space, is_len_between  # ✅ 길이 검사 헬퍼

def get_claude_response(
    unique_words: list,
    sentences: list,
    expressions: dict,
    parameters: dict,
    user_instructions: str,
    ref: str = '',
    *,
    min_length_no_space: int = 1700,
    max_length_no_space: int = 2000,
    max_retry: int = 5,
    model: str = "claude-opus-4-1-20250805",
    max_tokens: int = 3000
) -> str:
    """
    Claude로 원고 생성. 공백 제외 길이가 [min, max] 이내가 아니면 최대 max_retry까지 재시도.
    모두 실패 시 가장 근접한 결과 반환.
    """
    if not CLAUDE_API_KEY:
        raise ValueError("CLAUDE_API_KEY가 설정되지 않았습니다.")

    client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)

    words_str = ", ".join(unique_words) if unique_words else "없음"
    sentences_str = "\n- ".join(sentences) if sentences else "없음"
    expressions_str = json.dumps(expressions, ensure_ascii=False, indent=2) if expressions else "없음"
    parameters_str = json.dumps(parameters, ensure_ascii=False, indent=2) if parameters else "없음"

    prompt = f"""
    [고유 단어 리스트]
    {words_str}

    [문장 리스트]
    - {sentences_str}

    [표현 라이브러리 (중분류 키워드: [표현])]
    {expressions_str}

    [AI 개체 인식 및 그룹화 결과 (대표 키워드: [개체])]
    {parameters_str}

    [사용자 지시사항]
    {user_instructions}

    [참고 문서]
    {ref}

    [요청]
    {getKoPrompt(keyword=user_instructions)}
    """

    retry = 0
    best_result = None
    best_distance = float("inf")
    target = (min_length_no_space + max_length_no_space) / 2

    while retry < max_retry:
        try:
            resp = client.messages.create(
                model=model,
                max_tokens=max_tokens,  # ✅ 필수
                messages=[{"role": "user", "content": prompt}],
            )
            # anthropic SDK: message.content는 블록 리스트일 수 있음
            # 텍스트만 합쳐서 사용
            blocks = getattr(resp, "content", [])
            text_parts = []
            for b in blocks:
                # TextBlock: {"type": "text", "text": "..."}
                if isinstance(b, dict) and b.get("type") == "text":
                    text_parts.append(b.get("text", ""))
                elif hasattr(b, "type") and getattr(b, "type") == "text":
                    text_parts.append(getattr(b, "text", ""))
            text = "".join(text_parts).strip()

            n = length_no_space(text)
            print(f"[Claude 시도 {retry+1}] 공백 제외 길이: {n}")

            if is_len_between(text, min_length_no_space, max_length_no_space, inclusive=True):
                print("✅ Claude 조건 충족 — 문서 생성 완료")
                return text

            # 가장 근접한 결과 추적
            dist = abs(target - n)
            if dist < best_distance:
                best_distance = dist
                best_result = text

            print(f"⚠ Claude 길이 {min_length_no_space}~{max_length_no_space} 밖 — 재시도")
            retry += 1

        except Exception as e:
            print(f"Claude API 호출 중 오류: {e}")
            retry += 1

    print("⚠ Claude 최대 재시도 도달 — 가장 근접한 문서 반환")
    return best_result or ""