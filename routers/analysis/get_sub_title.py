from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from openai import OpenAI
from config import OPENAI_API_KEY
from constants.Model import Model

router = APIRouter(prefix="/analysis", tags=["analysis"])
client = OpenAI(api_key=OPENAI_API_KEY)

class SubtitleReq(BaseModel):
    text: str
    top_k: int = 7

class SubtitleRes(BaseModel):
    subtitles: list[str]
    domain_hints: dict[str, float]

@router.post("/sub-title", response_model=SubtitleRes)
async def get_sub_title(payload: SubtitleReq):
    prompt = f"""
다음 블로그 원고에서 **부제 5~{payload.top_k}개**와
도메인 핵심 키워드 10개를 중요도 가중치(0.4~1.2)와 함께 JSON으로 반환해.

- 부제는 지어내는 것이 아닌 있는 그대로 가져와야 합니다.

- 부제는 깔끔하고 간결해야 함.
- 도메인 키워드는 의미 있는 단어/구 단위여야 함.
- JSON 형식:
{{
  "subtitles": ["...", "..."],
  "domain_hints": {{"키워드1": 1.0, "키워드2": 0.8}}
}}

원고:
{payload.text}
"""
    try:
        resp = client.chat.completions.create(
            model=Model.GPT5_NANO,  # 가벼운 모델 가능
            messages=[{"role": "user", "content": prompt}],
        )
        content = resp.choices[0].message.content.strip()
        import json
        data = json.loads(content)
        return SubtitleRes(**data)
    except Exception as e:
        raise HTTPException(500, f"AI 추출 실패: {e}")