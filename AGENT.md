# 🤖 Blog Analyzer AI Agent

## 🎯 프로젝트 개요
**FastAPI 기반 블로그 원고 분석 및 AI 생성 도구**
- **언어**: Python 3.7+
- **주 목적**: 기존 원고 분석 → AI 기반 신규 원고 자동 생성
- **프레임워크**: FastAPI + Uvicorn
- **데이터베이스**: MongoDB (pymongo)
- **AI 서비스**: GPT-4/5, Claude, Gemini, Solar(Upstage)
- **자연어처리**: KoNLPy, KSS (한국어 특화)
- **CLI 도구**: Click

## 🏗️ 아키텍처

### 🖥️ CLI 도구 (main.py)
```bash
# 메뉴형 대화식 CLI - 분석부터 생성까지 전 과정
python main.py
```
**분석 파이프라인**: 형태소 분석 → 문장 분리 → 표현 추출 → 파라미터 분석 → 템플릿 생성 → 원고 생성

### 🌐 API 서버 (api.py)
```bash
# FastAPI 서버 - RESTful API 제공
uvicorn api:app --reload --host 0.0.0.0 --port 8000
```

### 📡 주요 API 엔드포인트
```
🤖 AI 원고 생성
POST /generate/gpt         # GPT-4 원고 생성
POST /generate/gpt_5       # GPT-5 원고 생성
POST /generate/claude      # Claude 원고 생성
POST /generate/gemini      # Gemini 원고 생성
POST /generate/solar       # Solar 원고 생성
POST /generate/kkk         # KKK 프롬프트 특화 생성
POST /generate/chunk       # 청크 단위 분할 생성
POST /generate/step_by_step # 단계별 생성

📊 텍스트 분석
POST /analysis/upload_text     # 텍스트 분석 업로드
POST /analysis/get_sub_title   # 부제목 추출

🗂️ 카테고리 관리
POST /category/keyword         # 키워드 카테고리 분류
```

---

## 📁 핵심 디렉토리 구조

```
blog_analyzer/
├── 🚀 main.py                 # CLI 메인 스크립트 (메뉴형)
├── 🌐 api.py                  # FastAPI 애플리케이션 진입점
├── ⚙️ config.py               # 환경변수 및 API 클라이언트 설정
├── 🗄️ mongodb_service.py      # MongoDB 연결 및 CRUD 서비스
├── 📡 routers/               # FastAPI 라우터들
│   ├── generate/             # 🤖 AI 원고 생성 라우터들
│   │   ├── gpt.py           # GPT-4 생성
│   │   ├── gpt_5.py         # GPT-5 생성
│   │   ├── claude.py        # Claude 생성
│   │   ├── gemini.py        # Gemini 생성
│   │   ├── solar.py         # Solar 생성
│   │   ├── kkk.py          # KKK 프롬프트 특화
│   │   ├── chunk.py        # 청크 분할 생성
│   │   └── step_by_step.py # 단계별 생성
│   ├── analysis/             # 📊 텍스트 분석 라우터들
│   └── category/             # 🗂️ 카테고리 관련 라우터들
├── 🧠 llm/                   # LLM 서비스 로직
│   ├── gpt_4_service.py     # GPT-4 구현체
│   ├── claude_service.py    # Claude 구현체
│   ├── gemini_service.py    # Gemini 구현체
│   ├── chunk_service.py     # 청크 처리 로직
│   └── kkk_service.py      # KKK 프롬프트 처리
├── 🔬 analyzer/              # 자연어 텍스트 분석 모듈
│   ├── morpheme.py          # 형태소 분석 (KoNLPy)
│   ├── sentence.py          # 문장 분리 (KSS)
│   ├── expression.py        # 표현 추출 (AI 기반)
│   └── parameter.py         # 파라미터 분석 (AI 기반)
├── 📄 schema/                # Pydantic 스키마 정의
├── 🛠️ utils/                 # 유틸리티 함수들
├── 💬 _prompts/              # AI 프롬프트 템플릿
├── 📊 _constants/            # 상수 정의 (모델명 등)
└── 📚 _docs/                 # 문서 관련 파일들
```

## 🔧 주요 기능 흐름

### 1️⃣ 텍스트 분석 파이프라인
```
📝 원고 텍스트 파일들
    ↓
🔬 1. 형태소 분석 (KoNLPy) → 단어 추출
    ↓
📏 2. 문장 분리 (KSS) → 문장 단위 분리
    ↓
🎨 3. 표현 추출 (AI) → 글쓰기 표현 패턴 추출
    ↓
🏷️ 4. 파라미터 분석 (AI) → 개체명 인식 및 그룹화
    ↓
📋 5. 템플릿 생성 → 파라미터를 변수화한 템플릿
    ↓
🗄️ MongoDB 저장 (분석 결과 축적)
```

### 2️⃣ AI 원고 생성 워크플로우
```
📊 사용자 키워드 + 참조 원고 (선택)
    ↓
🗄️ MongoDB에서 기존 분석 데이터 로드
    ↓
💬 프롬프트 생성 (시스템 + 사용자 + 분석 결과)
    ↓
🤖 AI 모델 호출 (GPT/Claude/Gemini/Solar)
    ↓
✨ 텍스트 후처리 및 정제
    ↓
🗄️ 생성 결과 MongoDB 저장 + API 응답
```

---

## 🎯 **Python 네이밍 컨벤션 (필수)**

### **1. 변수 & 함수 - snake_case**
```python
# ✅ 올바른 네이밍
user_name = "john"
user_list = ["john", "jane"]
is_logged_in = True
has_permission = False

# 함수 (동사 + 명사)
def get_user_info():
    pass

def create_review():
    pass

def update_content():
    pass

def handle_login_click():
    pass

# ❌ 잘못된 네이밍
userName = "john"          # camelCase 금지
userList = ["john"]        # camelCase 금지
isLoggedIn = True          # camelCase 금지
hasRef = False             # camelCase 금지
```

### **2. 클래스 - PascalCase**
```python
# ✅ 올바른 클래스명
class UserService:
    pass

class MongoDBService:
    pass

class GenerateRequest:
    pass

# ❌ 잘못된 클래스명
class userService:         # 소문자 시작 금지
class generate_request:    # snake_case 금지
```

### **3. 상수 - UPPER_SNAKE_CASE**
```python
# ✅ 올바른 상수명
OPENAI_API_KEY = "sk-..."
MONGO_URI = "mongodb://..."
MAX_TEXT_LENGTH = 3200
MIN_TEXT_LENGTH = 3000
DEFAULT_MODEL_NAME = "gpt-4"

# ❌ 잘못된 상수명
openai_api_key = "sk-..."  # 소문자 금지
maxTextLength = 3200       # camelCase 금지
```

### **4. 파일 & 모듈 - snake_case**
```python
# ✅ 올바른 파일명
gpt_service.py
claude_service.py
mongodb_service.py
text_cleaner.py
query_parser.py

# ❌ 잘못된 파일명
gptService.py              # camelCase 금지
ClaudeService.py           # PascalCase 금지
```

### **5. 비공개 변수/함수 - _leading_underscore**
```python
# ✅ 비공개 변수/함수
class AIService:
    def __init__(self):
        self._api_key = "secret"      # 비공개 변수
        self.__client = None          # 강한 비공개
    
    def _parse_response(self):        # 비공개 메서드
        pass
    
    def generate_text(self):          # 공개 메서드
        return self._parse_response()
```

---

## 🔧 **FastAPI 패턴 (표준화)**

### **1. 라우터 기본 템플릿**
```python
from fastapi import APIRouter, HTTPException
from fastapi.concurrency import run_in_threadpool

from mongodb_service import MongoDBService
from schema.generate import GenerateRequest
from utils.get_category_db_name import get_category_db_name
from llm.gpt_service import gpt_generate, MODEL_NAME

router = APIRouter()

@router.post("/generate/service")
async def generate_endpoint(request: GenerateRequest):
    """
    AI 원고 생성 엔드포인트
    """
    service = request.service.lower()
    keyword = request.keyword.strip()
    ref_content = request.ref
    
    category = get_category_db_name(keyword=keyword)
    
    # MongoDB 서비스 초기화
    db_service = MongoDBService()
    db_service.set_db_name(db_name=category)
    
    # 디버그 로깅
    is_ref = bool(ref_content and ref_content.strip())
    print(f"[GEN] service={service} | model={MODEL_NAME} | category={category} | keyword={keyword} | has_ref={is_ref}")
    
    try:
        # 비동기 AI 호출
        generated_text = await run_in_threadpool(
            gpt_generate, 
            user_instructions=keyword, 
            ref=ref_content
        )
        
        if generated_text:
            # MongoDB 저장
            document = {
                "content": generated_text,
                "timestamp": time.time(),
                "engine": MODEL_NAME,
                "keyword": keyword,
                "category": category,
            }
            
            db_service.insert_document("manuscripts", document)
            document["_id"] = str(document["_id"])
            
            return document
        else:
            raise HTTPException(
                status_code=500,
                detail="원고 생성에 실패했습니다."
            )
            
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"내부 오류: {e}")
    finally:
        db_service.close_connection()
```

### **2. 에러 처리 표준 패턴**
```python
try:
    # 메인 로직
    result = ai_service.generate(prompt)
    return result
    
except ValueError as e:
    # 사용자 입력 오류
    raise HTTPException(status_code=400, detail=str(e))
    
except ConnectionError as e:
    # 외부 서비스 연결 오류
    raise HTTPException(status_code=503, detail=f"서비스 연결 실패: {e}")
    
except Exception as e:
    # 예상치 못한 오류
    raise HTTPException(status_code=500, detail=f"내부 오류: {e}")
    
finally:
    # 리소스 정리 (필수)
    if db_service:
        db_service.close_connection()
```

---

## 🤖 **AI 서비스 패턴 (표준화)**

### **1. AI 서비스 함수 템플릿**
```python
import time
from typing import Optional

from config import OPENAI_API_KEY, openai_client
from _constants.models import GPT_MODEL
from _prompts.get_system_prompt import get_system_prompt
from utils.query_parser import parse_query
from utils.text_cleaner import comprehensive_text_clean
from utils.format_paragraphs import format_paragraphs

def ai_generate_text(user_instructions: str, ref_content: str = "", category: str = "") -> str:
    """
    AI 텍스트 생성 함수
    
    Args:
        user_instructions: 사용자 지시사항
        ref_content: 참조 원고 (선택적)
        category: 카테고리 (선택적)
    
    Returns:
        생성된 텍스트 (정제됨)
    
    Raises:
        ValueError: API 키 미설정, 키워드 없음 등
        RuntimeError: AI 응답 오류
        Exception: 기타 예외
    """
    
    # 1. API 키 검증
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY가 설정되어 있지 않습니다.")
    
    # 2. 쿼리 파싱
    parsed_query = parse_query(user_instructions)
    
    if not parsed_query["keyword"]:
        raise ValueError("키워드가 없습니다.")
    
    keyword = parsed_query["keyword"]
    
    # 3. 프롬프트 생성
    system_prompt = get_system_prompt(category=category)
    user_prompt = build_user_prompt(parsed_query, ref_content)
    
    # 4. AI 호출
    try:
        start_time = time.time()
        print(f"AI 생성 시작: {keyword}")
        
        response = openai_client.chat.completions.create(
            model=GPT_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )
        
        # 5. 토큰 사용량 로깅
        if hasattr(response, 'usage') and response.usage:
            prompt_tokens = response.usage.prompt_tokens
            completion_tokens = response.usage.completion_tokens
            total_tokens = response.usage.total_tokens
            print(f"토큰 사용량: in={prompt_tokens}, out={completion_tokens}, total={total_tokens}")
        
        # 6. 응답 검증
        if not response.choices or not response.choices[0].message:
            raise RuntimeError("AI가 유효한 응답을 반환하지 않았습니다.")
        
        generated_text = response.choices[0].message.content.strip()
        
        if not generated_text:
            raise RuntimeError("AI가 빈 응답을 반환했습니다.")
        
        # 7. 텍스트 후처리
        formatted_text = format_paragraphs(generated_text)
        cleaned_text = comprehensive_text_clean(formatted_text)
        
        # 8. 성능 로깅
        elapsed_time = time.time() - start_time
        text_length = len(cleaned_text.replace(" ", ""))
        print(f"AI 생성 완료: {elapsed_time:.2f}s, 길이: {text_length}자")
        
        return cleaned_text
        
    except Exception as e:
        print(f"AI 생성 오류: {e}")
        raise

def build_user_prompt(parsed_query: dict, ref_content: str) -> str:
    """사용자 프롬프트 구성"""
    keyword = parsed_query["keyword"]
    note = parsed_query.get("note", "")
    
    prompt = f"""
[개요]
{keyword}

위 키워드를 기반으로 원고를 작성해줘

{'[참조 원고]' if ref_content else ''}
{ref_content}

{'[추가 요구사항]' if note else ''}
{note}
""".strip()
    
    return prompt
```

---

## 📦 **Pydantic 스키마 패턴**

### **1. 요청/응답 스키마**
```python
from typing import Optional
from pydantic import BaseModel, Field

class GenerateRequest(BaseModel):
    """AI 원고 생성 요청 스키마"""
    service: str = Field(..., description="AI 서비스명")
    keyword: str = Field(..., min_length=1, description="생성 키워드")
    ref: str = Field("", description="참조 원고")

class GenerateResponse(BaseModel):
    """AI 원고 생성 응답 스키마"""
    content: str = Field(..., description="생성된 원고")
    timestamp: float = Field(..., description="생성 시간")
    engine: str = Field(..., description="사용된 AI 모델")
    keyword: str = Field(..., description="키워드")
    category: str = Field(..., description="카테고리")

class APIResponse(BaseModel):
    """공통 API 응답 스키마"""
    success: bool = Field(..., description="성공 여부")
    data: Optional[dict] = Field(None, description="응답 데이터")
    message: str = Field("", description="응답 메시지")
    timestamp: float = Field(..., description="응답 시간")
```

---

## 🗂️ **MongoDB 서비스 패턴**

### **1. 표준 MongoDB 사용 패턴**
```python
def save_generated_content(keyword: str, content: str, category: str):
    """생성된 컨텐츠 저장"""
    db_service = MongoDBService()
    db_service.set_db_name(db_name=category)
    
    try:
        document = {
            "content": content,
            "timestamp": time.time(),
            "keyword": keyword,
            "category": category,
        }
        
        result_id = db_service.insert_document("manuscripts", document)
        print(f"문서 저장 완료: {result_id}")
        
        return result_id
        
    except Exception as e:
        print(f"문서 저장 실패: {e}")
        raise
    finally:
        db_service.close_connection()
```

---

## 📋 **Import 순서 표준**

```python
# 1. Python 표준 라이브러리
import os
import time
import re
from typing import Optional, List, Dict, Any

# 2. 서드파티 라이브러리
from fastapi import APIRouter, HTTPException
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, Field
from openai import OpenAI

# 3. 프로젝트 내부 모듈 (알파벳 순)
from config import OPENAI_API_KEY, openai_client
from mongodb_service import MongoDBService
from schema.generate import GenerateRequest
from utils.get_category_db_name import get_category_db_name
from utils.query_parser import parse_query
from utils.text_cleaner import comprehensive_text_clean
```

---

## 🚨 **상수 관리 개선**

### **1. _constants/ 폴더 구조**
```python
# _constants/config.py
class TextConfig:
    MIN_LENGTH: int = 3000
    MAX_LENGTH: int = 3200
    MAX_LINE_LENGTH: int = 50
    PARAGRAPH_BREAK_COUNT: int = 2

# _constants/models.py  
class AIModels:
    GPT_4 = "gpt-4"
    GPT_5 = "gpt-5"
    CLAUDE_3 = "claude-3-sonnet"
    GEMINI_PRO = "gemini-pro"

# _constants/messages.py
class ErrorMessages:
    API_KEY_MISSING = "API 키가 설정되어 있지 않습니다."
    KEYWORD_MISSING = "키워드가 없습니다."
    EMPTY_RESPONSE = "AI가 빈 응답을 반환했습니다."
```

### **2. 상수 사용 예시**
```python
from _constants.config import TextConfig
from _constants.models import AIModels
from _constants.messages import ErrorMessages

# 사용
if len(text) < TextConfig.MIN_LENGTH:
    raise ValueError(f"텍스트 길이가 {TextConfig.MIN_LENGTH}자 미만입니다.")

model = AIModels.GPT_4

if not api_key:
    raise ValueError(ErrorMessages.API_KEY_MISSING)
```

---

## 🔍 **로깅 시스템 개선**

### **1. 로깅 설정**
```python
import logging
from typing import Optional

# utils/logger.py
def setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """로거 설정"""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger

# 각 모듈에서 사용
logger = setup_logger(__name__)
```

### **2. 로깅 사용 패턴**
```python
# print 대신 logger 사용
logger.info(f"AI 생성 시작: {keyword}")
logger.warning(f"참조 원고가 없습니다: {keyword}")
logger.error(f"AI 생성 실패: {error}")
logger.debug(f"토큰 사용량: {tokens}")
```

---

## 🎯 **개발 체크리스트**

### **✅ 변수/함수 네이밍**
- [ ] 모든 변수는 `snake_case`인가?
- [ ] 모든 클래스는 `PascalCase`인가?
- [ ] 모든 상수는 `UPPER_SNAKE_CASE`인가?
- [ ] camelCase 변수는 모두 제거했는가?

### **✅ 코드 구조**
- [ ] Import 순서가 표준에 맞는가?
- [ ] 타입 힌트를 사용했는가?
- [ ] 에러 처리가 적절한가?
- [ ] 리소스 정리를 finally에서 했는가?

### **✅ AI 서비스**
- [ ] API 키 검증을 했는가?
- [ ] 응답 검증을 했는가?
- [ ] 토큰 사용량을 로깅했는가?
- [ ] 텍스트 후처리를 했는가?

---

## 🚀 **변수명 일괄 수정 가이드**

### **수정해야 할 변수들**
```python
# ❌ 현재 → ✅ 수정 후
hasRef → has_ref
isRef → is_ref
userId → user_id
userName → user_name
apiKey → api_key
dbName → db_name
modelName → model_name
generatedText → generated_text
userInstructions → user_instructions
refContent → ref_content
```

나는! 나는..! 파이썬 컨벤션을 완벽하게 정리했다!! 🎯

이제 모든 camelCase 변수들을 snake_case로 바꾸면 완전히 파이썬스러운 코드가 될 거야!

잠시 소란이 있었어요~ 🎪