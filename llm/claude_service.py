import anthropic
from config import CLAUDE_API_KEY

def get_claude_response(prompt: str):
    """
    Claude API를 사용하여 주어진 프롬프트에 대한 응답을 생성합니다.

    Args:
        prompt (str): Claude 모델에 전달할 프롬프트 문자열

    Returns:
        str: 생성된 텍스트 응답
    """
    if not CLAUDE_API_KEY:
        raise ValueError("CLAUDE_API_KEY가 설정되지 않았습니다.")

    client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)
    print(prompt)
    try:
        message = client.messages.create(
            model='claude-opus-4-1-20250805',
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        content = message.content[0].text
        
        return content
    except Exception as e:
        print(f"Claude API 호출 중 오류 발생: {e}")
        return None