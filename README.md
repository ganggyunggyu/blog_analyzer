# Blog Content Factory

이 프로젝트는 블로그 콘텐츠 생성을 자동화하는 시스템입니다. 기존에 작성된 여러 블로그 게시물들을 분석해 데이터베이스를 구축하고, 이 데이터를 기반으로 다양한 LLM을 활용하여 새로운 원고를 만들어냅니다.

단순히 키워드를 LLM에 전달하는 것을 넘어, 기존 콘텐츠의 스타일과 핵심 정보를 재활용하여 더 깊이 있고 일관된 결과물을 얻는 것을 목표로 합니다.

---

## 개요

이 시스템의 작동 방식은 크게 두 단계로 나뉩니다.

1.  **콘텐츠 분석 및 데이터베이스 구축**
    먼저 `data/` 폴더에 있는 텍스트 파일들을 읽어들여 분석을 시작합니다. 이 과정에서 AI를 사용해 글의 핵심적인 요소들, 예를 들어 자주 언급되는 장소나 제품 같은 '개체(Parameters)'나 반복적으로 사용되는 '표현(Expressions)' 등을 추출합니다. 이렇게 추출된 정보는 문장, 핵심 단어 등과 함께 MongoDB에 저장되어 일종의 콘텐츠 데이터베이스를 형성합니다.

2.  **데이터 기반 원고 생성**
    새로운 원고를 생성할 때는 단순히 키워드만 사용하는 것이 아니라, 1단계에서 구축한 데이터베이스를 함께 활용합니다. 사용자가 키워드를 입력하면, 시스템은 AI를 통해 그 키워드에 가장 적합한 카테고리를 찾아내고 해당 카테고리의 데이터를 불러옵니다. 이 데이터를 컨텍스트로 삼아 GPT, Claude, Gemini 같은 LLM에게 원고 생성을 요청함으로써, 기존 콘텐츠의 맥락을 이해하는 결과물을 만들어냅니다.

---

## 주요 기능

-   **다양한 LLM 지원**: 필요에 따라 GPT, Claude, Gemini 등 여러 언어 모델 중 하나를 선택해 원고를 생성할 수 있습니다.
-   **콘텐츠 데이터베이스**: MongoDB를 데이터베이스로 사용해, 한번 분석한 콘텐츠의 자산(단어, 문장, 표현, 개체)을 지속적으로 축적하고 재사용합니다.
-   **AI 카테고리 분류**: 생성하려는 원고의 키워드를 AI가 스스로 판단하여, 가장 관련성 높은 데이터베이스를 선택해 사용합니다.
-   **유연한 실행 환경**: 자동화된 파이프라인을 위한 CLI 명령어와 외부 연동을 위한 REST API를 모두 지원합니다.

---

## 기술 스택

-   **Backend**: Python, FastAPI, Uvicorn
-   **CLI**: Click
-   **Database**: MongoDB (`pymongo`)
-   **AI / LLM**: `openai`, `anthropic`, `google-generativeai`
-   **NLP (Korean)**: `konlpy`, `kss`

---

## 시작하기

### 1. 환경 준비

이 프로젝트를 실행하려면 Python 3.7 이상 버전과 MongoDB 서버가 필요합니다.

먼저 git을 통해 프로젝트를 내려받고 해당 폴더로 이동합니다.

```bash
git clone <저장소_URL>
cd blog_analyzer
```

### 2. 설치

터미널에서 아래 명령어를 순서대로 실행하여 필요한 라이브러리를 설치하고, `blog-analyzer` 명령어를 등록합니다.

```bash
# 1. 파이썬 가상환경을 만들어 프로젝트 의존성을 독립적으로 관리합니다.
python3 -m venv venv
source venv/bin/activate

# 2. requirements.txt 파일에 기록된 라이브러리들을 설치합니다.
pip install -r requirements.txt

uvicorn api:app --reload --host 0.0.0.0 --port 8000

# 3. 프로젝트를 "편집 가능 모드"로 설치합니다.
# 이렇게 하면 코드를 수정했을 때 바로 반영되며, `blog-analyzer` 명령어를 사용할 수 있게 됩니다.
pip install -e .
```

### 3. 환경 변수 설정

LLM API 키를 등록해야 합니다. 프로젝트 폴더 최상단에 `.env` 파일을 만들고, 아래 형식에 맞게 자신의 API 키를 입력해주세요.

```
# .env 파일 내용
OPENAI_API_KEY="sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
ANTHROPIC_API_KEY="sk-ant-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
GEMINI_API_KEY="AIzaxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

---

## 사용 방법

이 프로젝트는 크게 세 가지 방식으로 사용할 수 있습니다.

### 방법 1: CLI 도구 사용

`blog-analyzer` 명령어를 통해 주요 기능을 실행할 수 있습니다.

**1단계: 데이터 분석**

`data` 폴더에 분석할 텍스트 파일들을 넣고, 아래 명령어를 실행하면 파일들을 분석해 MongoDB에 데이터베이스를 구축합니다.

```bash
blog-analyzer analyze
```

**2단계: 원고 생성**

데이터베이스가 준비되면, 키워드를 지정해 새 원고를 만들 수 있습니다.

```bash
# --keywords: 원고의 주제 (필수)
# --user-instructions: 결과물의 톤이나 스타일에 대한 추가 요청 (선택)
blog-analyzer generate --keywords "강남역 맛집" --user-instructions "20대 여성이 좋아할 만한 트렌디한 곳으로 추천해줘"
```

### 방법 2: API 서버 실행

외부 서비스와 연동해야 할 경우, API 서버를 실행할 수 있습니다.

**서버 실행**

아래 명령어를 실행하면 `0.0.0.0:8000` 주소에서 서버가 시작됩니다. 이 명령어는 터미널 창을 계속 차지하고 실행 상태를 보여주는 포그라운드(foreground) 방식으로 작동합니다.

```bash
blog-analyzer serve
```

서버가 실행되면 아래와 같은 로그가 터미널에 나타납니다.
```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

**서버 중지**

서버를 중지하려면, 서버가 실행되고 있는 터미널 창에서 `Ctrl+C` 키를 누르면 됩니다.

**API 요청**

서버가 실행 중일 때, `curl` 같은 도구를 사용해 원고 생성을 요청할 수 있습니다.

-   **Endpoints**: `POST /generate/gpt`, `POST /generate/gemini`, `POST /generate/claude`
-   **`curl` 예시**:

    ```bash
    curl -X POST http://127.0.0.1:8000/generate/gpt \
    -H "Content-Type: application/json" \
    -d '{
      "service": "gpt",
      "keyword": "제주도 애월 카페 추천",
      "ref": "https://example.com/jeju-cafe-review"
    }'
    ```

### 방법 3: 대화형 모드

각 분석 기능을 하나씩 테스트해보고 싶을 때는 `main.py` 파일을 직접 실행하여 대화형 모드를 사용할 수 있습니다.

```bash
python main.py
```

위 명령어를 실행하면 터미널에 각 기능별 메뉴가 나타나며, 번호를 선택해 원하는 기능만 개별적으로 실행해볼 수 있습니다.
