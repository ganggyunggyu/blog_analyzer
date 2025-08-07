from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from main import run_manuscript_generation
from mongodb_service import MongoDBService

app = FastAPI()

class GenerateRequest(BaseModel):
    keywords: str
    user_instructions: str = ""

@app.post("/generate-manuscript")
async def generate_manuscript_api(request: GenerateRequest):
    db_service = None
    try:
        db_service = MongoDBService()
        analysis_data = db_service.get_latest_analysis_data()
        

        unique_words = analysis_data.get("unique_words", [])
        sentences = analysis_data.get("sentences", [])
        expressions = analysis_data.get("expressions", {})
        parameters = analysis_data.get("parameters", {})

        print(unique_words, sentences, expressions, parameters)
        if not (unique_words and sentences and expressions and parameters):
            raise HTTPException(status_code=500, detail="MongoDB에 원고 생성을 위한 충분한 분석 데이터가 없습니다. 먼저 분석을 실행하고 저장해주세요.")

        generated_manuscript = run_manuscript_generation(
            unique_words=unique_words,
            sentences=sentences,
            expressions=expressions,
            parameters=parameters,
            user_instructions=request.user_instructions
        )
        
        if generated_manuscript:
            return {"manuscript": generated_manuscript}
        else:
            raise HTTPException(status_code=500, detail="원고 생성에 실패했습니다. AI 모델 응답을 확인해주세요.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"원고 생성 중 오류 발생: {e}")
    finally:
        if db_service:
            db_service.close_connection()
