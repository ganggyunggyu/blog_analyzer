from config import openai_client
def send_prompt_to_gpt(keyword):
    
    
    try:
        response = openai_client.chat.completions.create(
            model='gpt-4.1-2025-04-14',
            messages=[
                {"role": "system", "content": ''},
                {"role": "user", "content": ''}
            ],
            temperature=0.0,
            top_p=1.0,
            presence_penalty=0.0
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"An error occurred: {e}"
