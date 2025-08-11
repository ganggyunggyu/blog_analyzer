from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from main import run_manuscript_generation
from mongodb_service import MongoDBService
from llm.claude_service import get_claude_response
from llm.gemini_service import get_gemini_response
from utils.categorize_keyword_with_ai import categorize_keyword_with_ai
from typing import Optional



app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
class GenerateRequest(BaseModel):
    service: str
    keyword: str
    ref: Optional[str] = None
    
    
@app.get("/test")
async def test_endpoint():
    return {"message": "Test successful"}


@app.post("/generate/gpt")
async def generate_manuscript_api(request: GenerateRequest):
    """
    Generates text using the specified service (gpt, claude, or solar).
    """
    service = request.service.lower()
    keyword = request.keyword.strip()
    ref = request.ref
    print(service, request)

    category = categorize_keyword_with_ai(keyword=keyword)

    db_service = MongoDBService()
    db_service.set_db_name(db_name=category)

    print(db_service.db._name)

    try:
        analysis_data = db_service.get_latest_analysis_data()
        unique_words = analysis_data.get("unique_words", [])
        sentences = analysis_data.get("sentences", [])
        expressions = analysis_data.get("expressions", {})
        parameters = analysis_data.get("parameters", {})

        
        if not (unique_words and sentences and expressions and parameters):
            raise HTTPException(status_code=500, detail="MongoDB에 원고 생성을 위한 충분한 분석 데이터가 없습니다. 먼저 분석을 실행하고 저장해주세요.")

        generated_manuscript = run_manuscript_generation(
            unique_words=unique_words,
            sentences=sentences,
            expressions=expressions,
            parameters=parameters,
            user_instructions=keyword,
            ref=ref
        )
        
        if generated_manuscript:
            import time
            current_time = time.time()
            document = {
                'content' : generated_manuscript,
                'timestamp': current_time,
            }
            try: 
                db_service.insert_document("manuscripts", document)
                document['_id'] = str(document['_id'])

                return document
            except Exception as e:
                print(f"데이터베이스에 저장 실패: {e}")
        else:
            raise HTTPException(status_code=500, detail="원고 생성에 실패했습니다. AI 모델 응답을 확인해주세요.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"원고 생성 중 오류 발생: {e}")
    finally:
        if db_service:
            db_service.close_connection()

@app.post("/generate/gemini")
def test_gemini_endpoint(prompt_data: GenerateRequest):
    try:
        prompt = prompt_data.keyword
        if not prompt:
            raise HTTPException(status_code=400, detail="'prompt' 필드는 필수입니다.")
        
        response = get_gemini_response(prompt)
        
        if response:
            return {"response": response}
        else:
            raise HTTPException(status_code=500, detail="Gemini API로부터 응답을 받지 못했습니다.")
            
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"서버 내부 오류: {e}")

@app.post("/generate/claude")
def test_claude_endpoint(req: GenerateRequest):
    try:
        prompt = req.keyword
        if not prompt:
            raise HTTPException(status_code=400, detail="'prompt' 필드는 필수입니다.")
        
        response = get_claude_response(prompt)
        
        if response:
            return {"content": response}
        else:
            raise HTTPException(status_code=500, detail="Claude API로부터 응답을 받지 못했습니다.")
            
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"서버 내부 오류: {e}")


