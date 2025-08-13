import logging, json, re
from openai import OpenAI
from config import OPENAI_API_KEY
from constants.Model import Model
from mongodb_service import MongoDBService
from fastapi import HTTPException

from prompts.get_gpt_prompt import GptPrompt


def manuscript_generator(
    user_instructions: str,
    ref: str = ""
) -> str:
    """
    분석 산출물 + 사용자 지시 → 원고 텍스트
    DB, 카테고리 등 외부 의존성 없음 (순수 함수).
    [단어 라이브러리]
    {unique_words}
    
    [문장 라이브러리]
    {sentences}
    """

    if not OPENAI_API_KEY:
        print("OPENAI_API_KEY 미설정")
        raise ValueError("OPENAI_API_KEY가 필요합니다.")
    
    model = Model.GPT4_1
    user_prompt = GptPrompt.gpt_4(keyword=user_instructions)

    db_service = MongoDBService()
    
    analysis_data = db_service.get_latest_analysis_data()
    unique_words = analysis_data.get('unique_words', [])
    sentences = analysis_data.get("sentences", [])
    expressions = analysis_data.get("expressions", {})
    parameters = analysis_data.get("parameters", {})

    # if not (unique_words and sentences and expressions and parameters):
    #     raise HTTPException(status_code=500, detail="MongoDB에 원고 생성을 위한 충분한 분석 데이터가 없습니다. 먼저 분석을 실행하고 저장해주세요.")

    expressions_str = json.dumps(expressions, ensure_ascii=False, indent=2) if expressions else "없음"
    parameters_str  = json.dumps(parameters, ensure_ascii=False, indent=2) if parameters else "없음"

    prompt = f"""

    [표현 라이브러리]
    {expressions_str}

    [AI 개체 인식 및 그룹화 결과]
    {parameters_str}

    [사용자 지시사항]
    {user_instructions}

    [참고 문서]
    {ref}

    [요청]
    {user_prompt}
    """.strip()

    client = OpenAI(api_key=OPENAI_API_KEY)
    try:
        print(f"GPT 생성 시작 | keyword={user_instructions}")
        res = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a professional blog post writer."},
                {"role": "user", "content": prompt}
            ],
            # max_completion_tokens=2200
        )
        usage = res.usage
        print(f"tokens in={usage.prompt_tokens}, out={usage.completion_tokens} total={usage.total_tokens}")
        

        text = (res.choices[0].message.content or "").strip()
        if not text:
            raise RuntimeError("모델이 빈 응답을 반환했습니다.")
        
        length_no_space = len(re.sub(r"\s+", "", text))
        print(f'{model} 문서 생성 완료 (공백 제외 길이: {length_no_space})')

        return text

    except Exception as e:
        print("OpenAI 호출 실패")
        print(e)
        raise