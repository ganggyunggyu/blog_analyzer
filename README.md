# Blog Analyzer

멀티 AI 엔진으로 네이버 블로그용 원고를 자동 생성·분석하는 FastAPI 기반 백엔드입니다.  
GPT, Claude, Gemini, SOLAR, Grok을 한 곳에서 제어하고, 카테고리별 MongoDB 데이터와 참조 원고를 섞어서 “사람이 쓴 것 같은 후기형 글”을 뽑아내는 게 목적입니다.

---

## 1. 개요

Blog Analyzer는 다음 시나리오를 타겟으로 합니다.

1. **키워드 & 카테고리 입력**
2. 카테고리별 MongoDB에서 **상위 노출 글·키워드 패턴** 조회
3. 필요하면 **참조 원고(ref)**까지 함께 투입
4. 선택한 AI 엔진(GPT / Claude / Gemini / SOLAR / Grok)으로 원고 생성
5. 생성된 텍스트를 **형태소·문장·표현 패턴 분석** 후 DB에 저장

FastAPI + Uvicorn 기반의 비동기 API 서버로 구성되어 있으며, ASGI 프레임워크 특성상 높은 동시성을 지원합니다. [oai_citation:0‡위키백과](https://en.wikipedia.org/wiki/Comparison_of_server-side_web_frameworks?utm_source=chatgpt.com)

---

## 2. 주요 기능

### 2.1 콘텐츠 생성

- **멀티 AI 엔진 지원**

  - OpenAI GPT-4 / GPT-5 (Responses API) [oai_citation:1‡Microsoft Learn](https://learn.microsoft.com/en-us/azure/ai-foundry/openai/how-to/responses?utm_source=chatgpt.com)
  - Anthropic Claude (Sonnet 계열)
  - Google Gemini (2.5 / 2.0 Flash 계열)
  - Upstage SOLAR (한국어 특화)
  - xAI Grok (reasoning 중심)

- **카테고리 맞춤 프롬프트**

  - 40개+ 카테고리별로 **별도 프롬프트 파일** 보유
  - 맛집 / 다이어트 / 의료 / 인테리어 / 공항 주차대행 / 애니 리뷰 등
  - 각 카테고리는 tone, 구조, 금지 표현, 필수 요소를 따로 정의

- **SEO & 네이버 최적화**

  - 키워드 자연스러운 삽입
  - 제목·소제목에 변형 키워드 분산 배치
  - 과도한 키워드 반복/광고체/AI티 제거 규칙 포함

- **참조 원고 기반 스타일 모방**
  - MongoDB에 저장된 상위 노출 글 / 수집한 ref 원고를 합쳐
    “이 카테고리에서 실제로 상위에 떠 있는 글의 문체”를 따라감

### 2.2 텍스트 분석

- **소제목 추출 / 재구성**
- **문장 분리 / 줄바꿈 규칙 적용**
- **형태소 분석 (KoNLPy, KSS 등 사용)**
- **표현 패턴 / 템플릿 추출**
- 분석 결과 역시 MongoDB에 저장해서 재학습에 사용

### 2.3 운영 편의 기능

- **청크 분할 생성**
  - 2~4개 청크로 나눠 생성 후 합치는 방식 지원
- **단계별 생성**
  - 개요 → 소제목 → 본문 순으로 점진 생성
- **배치 처리**
  - JSONL 기반 대량 생성 API/CLI 제공
- **동시 호출 제한**
  - 세마포어로 LLM 동시 요청 수를 제어 (기본 3개)

---

## 3. 기술 스택

### 3.1 Backend

- **FastAPI** (Python ASGI 웹 프레임워크) [oai_citation:2‡위키백과](https://en.wikipedia.org/wiki/Comparison_of_server-side_web_frameworks?utm_source=chatgpt.com)
- **Uvicorn** (ASGI 서버)
- **Python 3.12 권장**

### 3.2 LLM / AI

- OpenAI API – GPT-4 Turbo / GPT-5 Responses API [oai_citation:3‡Microsoft Learn](https://learn.microsoft.com/en-us/azure/ai-foundry/openai/how-to/responses?utm_source=chatgpt.com)
- Anthropic Claude
- Google Gemini
- Upstage SOLAR
- xAI Grok

### 3.3 NLP

- KoNLPy (형태소 분석)
- KSS (문장 분리)

### 3.4 Database

- **MongoDB / MongoDB Atlas** – 카테고리별 DB 분리 전략 사용 [oai_citation:4‡위키백과](https://ru.wikipedia.org/wiki/MongoDB?utm_source=chatgpt.com)

---

## 4. 아키텍처 & 데이터 흐름

### 4.1 전체 흐름

1. 클라이언트가 `/generate/...` 엔드포인트로 요청 전송
2. FastAPI 라우터가 Pydantic 스키마로 요청 검증
3. `llm/` 서비스에서:
   - 카테고리별 프롬프트 불러오기 (`_prompts/category/...`)
   - MongoDB에서 카테고리 DB 접속 후 상위 노출 데이터 조회
   - 참조 원고(ref)와 합쳐 최종 system / user prompt 구성
4. 선택된 AI 엔진 호출 (GPT / Claude / Gemini / SOLAR / Grok)
5. 응답 텍스트를 `utils/text_cleaner.py`, `ai_lib/line_break_service.py` 등으로 후처리
6. `generated` 컬렉션에 결과 저장 (content, 모델, 카테고리, 키워드 등)

### 4.2 카테고리별 DB 분리 전략

MongoDB에서 각 카테고리를 **별도 데이터베이스**로 분리해서 관리합니다.

- 예시:
  - `맛집_db`
  - `다이어트_db`
  - `공항_장기주차장_주차대행_db`
  - `anime_db`
- 공통으로 `generated` 컬렉션에서 생성 결과를 관리하고,
  `articles`, `keywords`, `analysis` 등은 카테고리 용도에 맞춰 씀.

이 구조 덕분에:

- 카테고리별 인덱싱·백업이 쉬움
- 특정 카테고리만 따로 실험 가능
- 나중에 카테고리 단위로 Atlas 클러스터를 분리하는 것도 자연스러움

---

## 5. 디렉터리 구조

요약 버전만 적으면:

```bash
blog_analyzer/
├── api.py                # FastAPI 엔트리 포인트
├── config.py             # 환경변수 / AI 클라이언트 설정
├── mongodb_service.py    # MongoDB CRUD 래퍼
├── cli.py                # 배치 실행용 CLI
│
├── routers/              # FastAPI 라우터 계층
│   ├── generate/         # 원고 생성 관련 API
│   ├── analysis/         # 텍스트 분석 API
│   ├── category/         # 키워드/카테고리 API
│   └── ref/              # 참조 원고 조회
│
├── llm/                  # LLM 호출 비즈니스 로직
│   ├── kkk_service.py    # 멀티 AI 엔진 통합 서비스 (핵심)
│   ├── gpt_4_v2_service.py
│   ├── gpt_5_v2_service.py
│   ├── claude_service.py
│   ├── gemini_service.py
│   └── chunk_service.py
│
├── _prompts/             # 프롬프트 엔지니어링 모음
│   ├── category/         # 카테고리별 프롬프트
│   ├── service/          # Mongo, ref 통합용 시스템 프롬프트
│   └── rules/            # 공통 금기/줄바꿈 규칙
│
├── analyzer/             # 텍스트 분석 모듈
├── ai_lib/               # 줄바꿈 등 AI 보조 로직
├── utils/                # 공용 유틸
├── schema/               # Pydantic 스키마
└── _constants/           # 모델 상수 등


⸻

6. 설치 및 실행

6.1 로컬 개발 환경

# 1. 클론
git clone https://github.com/ganggyunggyu/blog_analyzer.git
cd blog_analyzer

# 2. 가상환경
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. 패키지 설치
pip install -r requirements.txt

6.2 환경 변수 설정

프로젝트 루트에 .env 파일 생성:

# OpenAI
OPENAI_API_KEY=sk-...

# Anthropic Claude
ANTHROPIC_API_KEY=...

# Google Gemini
GEMINI_API_KEY=...

# Upstage SOLAR
UPSTAGE_API_KEY=...

# xAI Grok
GROK_API_KEY=...

# MongoDB
MONGO_URI=mongodb+srv://...
MONGO_DB_NAME=default_db   # 기본 DB명 (카테고리별로 set_db_name으로 교체)

# LLM 동시 호출 개수
LLM_CONCURRENCY=3

6.3 서버 실행

uvicorn api:app --reload --host 0.0.0.0 --port 8000

실행 후:
	•	Swagger: http://localhost:8000/docs
	•	OpenAPI JSON: http://localhost:8000/openapi.json

⸻

7. API 사용 예시

7.1 KKK 멀티 AI 서비스

하나의 엔드포인트에서 GPT / Claude / Gemini를 교체해서 쓸 수 있는 통합 서비스.

POST /kkk/generate
Content-Type: application/json

요청 예시:

{
  "service": "다이어트",
  "keyword": "위고비 다이어트 후기 부작용",
  "ref": ""
}

	•	service : 카테고리 이름 (프롬프트 + MongoDB DB 이름과 매핑)
	•	keyword: 블로그 원고의 메인 키워드
	•	ref    : 선택. 상위 노출 글 등을 그대로 넣어 스타일을 따라 쓰게 할 때 사용

사용 모델은 llm/kkk_service.py 내부에서 설정:

MODEL_NAME = "gpt-5o"  # gpt-4-turbo, claude-sonnet-4.5, gemini-2.5-flash-lite 등

7.2 GPT-4 전용

POST /gpt-4-v2/generate

{
  "service": "맛집",
  "keyword": "성수 맛집 예약",
  "ref": "수집해둔 상위 노출 글 전문 텍스트..."
}

7.3 텍스트 분석

소제목 추출

POST /analysis/get-sub-title
Content-Type: application/json

{
  "text": "분석할 블로그 원고 전체 텍스트..."
}

텍스트 파일 업로드 분석

POST /analysis/upload-text
Content-Type: multipart/form-data
file: blog.txt


⸻

8. 카테고리 시스템

8.1 구조

각 카테고리 프롬프트 파일은 다음 요소를 가진다.
	•	content_essence : 글의 본질(어떤 독자, 어떤 상황, 어떤 목적)
	•	writing_style   : 말투, 감정 농도, 존댓말/반말
	•	narrative_structure : 글 흐름 (도입 → 경험 → 디테일 → 한줄 정리 등)
	•	linguistic_patterns : 자주 쓰는 표현 / 피해야 할 표현
	•	key_components  : 필수 포함 요소 (가격, 위치, 부작용, 대안 등)
	•	emotional_arc   : 감정선 (불안 → 안도, 호기심 → 확신 등)
	•	transformation_examples : 좋은 예 / 나쁜 예 비교

8.2 실제 사용 예
	•	다이어트 카테고리
	•	위고비 / 마운자로 / 일반 식단 다이어트 등 다양한 케이스를 다룰 수 있게 설계
	•	“살 빼야지 → 정보 검색 → 시도 → 부작용/후기 → 내 결론” 흐름을 기본값으로 사용
	•	맛집 카테고리
	•	위치·주차·대기시간·가격·대표메뉴·실제 방문 동선 등
	•	사진 설명 없이도 포스팅이 성립되도록 문장 중심 서술
	•	공항_장기주차장_주차대행
	•	공식 주차장 vs 사설 대행비 비교
	•	맡기고 돌아올 때까지 타임라인 기준으로 서술

⸻

9. MongoDB 연동 패턴

9.1 기본 사용

from mongodb_service import MongoDBService

db = MongoDBService()
db.set_db_name("맛집")  # 카테고리 DB 선택

try:
    # 생성된 글 저장
    db.insert_document(
        collection_name="generated",
        document={
            "content": generated_text,
            "engine": "gpt-5o",
            "category": "맛집",
            "keyword": "성수 맛집 예약",
            "created_at": time.time()
        },
    )

    # 참조용 상위 노출 글 조회
    refs = db.find_documents(
        collection_name="articles",
        query={"keyword": "성수 맛집 예약"},
        limit=5,
    )

finally:
    db.close_connection()

9.2 전체 카테고리 검색 전략

현재 구조는 “카테고리별 DB 분리”라서, 전체 검색을 하고 싶으면:
	1.	utils/get_category_db_name.py에 등록된 카테고리 목록을 가져온다.
	2.	각 카테고리에 대해:
	•	set_db_name(category_db) 호출
	•	generated 또는 articles 컬렉션에서 동일 쿼리 실행
	3.	결과를 하나의 리스트로 합쳐서 반환

규모가 커지면:
	•	검색 전용 공통 DB (search_index)를 두고,
	•	생성 시점에 요약 정보(카테고리, 키워드, 제목, 주요 토픽)만 search_index에 동시에 적어두고
	•	검색 API는 search_index만 치는 식으로 스케일링 가능하다.

⸻

10. 개발 컨벤션
	•	Pydantic 스키마로 모든 요청/응답 타입 명시
	•	FastAPI 엔드포인트에서는 비즈니스 로직 금지, llm/ 및 analyzer/ 레이어로 위임
	•	동기 CPU 바운드 작업은 run_in_threadpool로 감싸서 이벤트 루프 블로킹 방지
	•	MongoDB 연결은 항상 try / finally로 감싸서 close_connection() 보장
	•	LLM 호출 에러 처리:
	•	사용자의 잘못된 입력 → HTTPException(status_code=400)
	•	외부 API/서버 에러 → HTTPException(status_code=500)

⸻

11. 실제 사용 시나리오 예시

11.1 성형·피부 시술 후기 자동 생성
	1.	service = "리쥬란"
	2.	키워드: "리쥬란 힐러 효과 개인후기"
	3.	ref: 해당 병원/시술 상위 노출 3개 원고 합본
	4.	kkk/generate 또는 gpt-5-v2/generate 호출
	5.	생성된 글을 검토 후, 그대로 네이버 블로그에 업로드

11.2 다이어트 인포/경험 혼합형 글 생성
	1.	service = "위고비"
	2.	키워드: "위고비 다이어트 부작용 비용"
	3.	MongoDB에서 위고비 관련 상위 노출 글의 정보·수치(가격범위, 부작용 빈도)를 추출
	4.	LLM 프롬프트에 실제 범위값을 포함해
“체험담 + 정보 글” 구조로 생성

11.3 맛집 체인 통합 운영
	1.	각 지점별 DB(예: 성수맛집, 서면맛집)에 리뷰 데이터를 쌓는다.
	2.	체인 전체에 대한 마케팅 글 작성 시,
여러 DB에서 공통 패턴을 뽑아 통합 프롬프트를 구성.
	3.	“지점별 공통 장점 + 지역별 차이점”을 살린 체인 브랜딩 글 생성.

⸻

12. 참고 링크

GitHub Repository: https://github.com/ganggyunggyu/blog_analyzer

FastAPI Docs:      https://fastapi.tiangolo.com/
OpenAI Responses:  https://platform.openai.com/docs/api-reference/responses
MongoDB Atlas:     https://www.mongodb.com/atlas

```
