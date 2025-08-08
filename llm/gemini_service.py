
from openai import OpenAI
from config import GEMINI_API_KEY


def get_gemini_response(prompt: str):
    """
    Gemini API를 사용하여 주어진 프롬프트에 대한 응답을 생성합니다.

    Args:
        prompt (str): Gemini 모델에 전달할 프롬프트 문자열

    Returns:
        str: 생성된 텍스트 응답
    """
    client = OpenAI(api_key=GEMINI_API_KEY)
    try:
        response = client.chat.completions.create(
            model='gemini-2.5-pro',
            messages=[
                {"role": "system", "content": ''},
                {"role": "user", "content": f'''{prompt}'''}
            ],
            temperature=0.0,
            top_p=1.0,
            presence_penalty=0.0
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"An error occurred: {e}"
