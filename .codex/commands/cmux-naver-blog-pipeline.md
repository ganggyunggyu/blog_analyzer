# cmux Naver Blog Pipeline

## 목적

API 엔드포인트를 직접 호출하지 않고, Codex 세션과 `cmux` 브라우저 surface를 중심으로 아래 흐름을 수행한다.

1. 네이버에서 키워드 검색
2. 상위 블로그 글 수집
3. 제목/도입부/소제목/문단 길이/이미지 배치/키워드 반복 패턴 분석
4. 분석 결과를 바탕으로 Claude용 원고 프롬프트 작성
5. Claude 세션에 프롬프트 전달
6. 이미지 준비
7. 네이버 에디터에 원고와 이미지를 배치

## 이 커맨드를 써야 하는 경우

- 사용자가 `cmux` 기반으로 네이버 상위글을 읽고 분석해서 원고를 만들고 싶다고 할 때
- 기존 `/generate/*` API 대신 Codex 세션 자체로 수집/분석/프롬프트 조립을 하고 싶을 때
- 브라우저에서 실제 검색 결과와 네이버 에디터 UI를 source of truth 로 써야 할 때

## 핵심 원칙

- 원고 생성용 백엔드 API는 호출하지 않는다.
- 검색과 수집은 `cmux browser`를 기본으로 쓴다.
- 네이버 로그인 상태, 파일 업로드, 에디터 커서/배치가 불안정하면 OpenClaw를 fallback으로 쓴다.
- 상위글의 문장 베끼기는 금지하고, 구조 패턴과 검색 의도만 추출한다.
- 프롬프트와 분석 결과는 항상 로컬 산출물로 남긴다.

## 모델 메모

- 로컬에서 확인한 Claude CLI 모델 선택지는 `claude-sonnet-4-6` 과 `claude-opus-4-5-20251101` 사용이 가능하다.
- 사용자가 `4.6 오푸스` 라고 말하면 모델명이 섞였을 가능성이 있으므로, 실제 실행 전 `Sonnet 4.6` 과 `Opus 4.5` 중 무엇을 원하는지 확인한다.

## 권장 산출물 경로

- `.coordination/naver_blog_pipeline/<timestamp>/search_notes.md`
- `.coordination/naver_blog_pipeline/<timestamp>/collected_posts.json`
- `.coordination/naver_blog_pipeline/<timestamp>/analysis.md`
- `.coordination/naver_blog_pipeline/<timestamp>/analysis.json`
- `.coordination/naver_blog_pipeline/<timestamp>/claude_prompt.md`
- `.coordination/naver_blog_pipeline/<timestamp>/draft.txt`
- `.coordination/naver_blog_pipeline/<timestamp>/image_plan.md`

## 실행 절차

### 0. 세션 준비

- `cmux new-workspace` 또는 기존 workspace 선택
- 브라우저 surface 하나와 터미널 surface 하나를 준비
- 필요하면 workspace 이름을 키워드 기준으로 변경

예시:

```bash
cmux new-workspace --cwd /Users/ganggyunggyu/Programing/21lab/text-gen-hub
cmux browser open "https://search.naver.com/search.naver?where=view&query=위고비%20가격"
```

### 1. 네이버 검색 결과 수집

- `where=view` 검색 결과를 기본으로 사용
- 광고성 랜딩, 쇼핑, 지식인, 뉴스는 제외하고 블로그성 결과를 우선 수집
- 최소 5개, 권장 8~10개 글을 본다
- 각 결과에서 아래 항목을 뽑는다

필수 수집 항목:

- 검색 결과 제목
- 검색 결과 요약문
- 본문 제목
- 본문 전체 길이 대략값
- 소제목 개수와 형식
- 이미지 개수와 배치 위치
- 첫 3문단 리듬
- 끝 2문단 마무리 방식
- 가격/비용/처방/비교/후기 중 어떤 의도에 초점을 두는지

`cmux browser snapshot`, `cmux browser get text`, `cmux browser click`, `cmux browser tab list` 조합으로 진행한다.

### 2. 상위글 구조 분석

수집한 글을 보고 아래 항목을 정리한다.

- 제목 길이 평균
- 메인 키워드 정확 일치 여부
- 서브 키워드 묶음 패턴
- 도입부에서 신뢰를 만드는 방식
- 번호형 소제목 사용 여부
- 가격 언급 위치와 방식
- 비교 대상이 등장하는 시점
- 실제 경험담처럼 보이게 만드는 표현
- 과장 문구, 금지해야 할 표현
- 이미지가 들어가는 대표 위치

분석 결과는 반드시 `analysis.md` 와 `analysis.json` 두 형태로 저장한다.

### 3. Claude용 프롬프트 작성

프롬프트는 아래 블록을 포함한다.

- 작업 목표
- 메인 키워드
- 수집 글 요약
- 검색 의도 분석
- 제목 방향 3개
- 본문 구조 가이드
- 금지 표현
- 반드시 포함할 정보
- 이미지 배치 계획
- 네이버 블로그 말투 기준

프롬프트에는 원문 복붙 대신 아래처럼 추상화된 분석만 넣는다.

예시:

```md
상위글 8건 중 6건이 도입부 첫 4문장 안에 비용 부담과 처방 조건을 함께 언급함.
제목은 비교형보다 현실 확인형이 많았고, 평균 길이는 19~24자 수준이었음.
가격형 글도 약값 단독이 아니라 진료비, 유지비, 용량 상승에 따른 총비용을 함께 적는 패턴이 강했음.
이미지는 제목 아래 1장, 중간 비교 섹션 1장, 마무리 직전 1장 배치가 가장 많았음.
```

### 4. Claude 세션 handoff

권장 방식은 둘 중 하나다.

1. `claude -p` 로 단발 생성
2. `claude` 인터랙티브 세션을 별도 terminal surface 에 띄우고 프롬프트를 전달

예시:

```bash
claude --model claude-sonnet-4-6 -p "$(cat .coordination/naver_blog_pipeline/<timestamp>/claude_prompt.md)"
```

또는

```bash
claude --model claude-opus-4-5-20251101
```

그다음 `cmux send` 로 프롬프트를 전달한다.

### 5. 이미지 준비

이미지 단계는 두 갈래 중 하나를 선택한다.

1. Codex 세션에서 이미지 생성 스킬을 사용해 직접 생성
2. 브라우저에서 참고 이미지를 수집하고 로컬 자산으로 정리

이미지 계획에는 아래를 포함한다.

- 필요한 이미지 수
- 각 이미지의 위치
- 필요한 구도
- 텍스트 오버레이 여부
- 파일명 규칙

### 6. 네이버 에디터 배치

- 네이버 글쓰기 페이지를 연다
- 제목 입력
- 본문 붙여넣기
- 이미지 업로드
- 이미지 배치를 `도입부 아래 / 핵심 비교 구간 / 마무리 직전` 순으로 우선 검토
- 미리보기 또는 실제 에디터 화면 기준으로 줄바꿈, 공백, 이미지 순서를 재확인

에디터 단계에서 아래 문제가 생기면 fallback 을 쓴다.

- 파일 선택기 포커스 이탈
- 로그인 세션 꼬임
- iframe 내부 클릭 실패
- 붙여넣기 후 줄바꿈 붕괴

이 경우 OpenClaw 브라우저 또는 macOS 네이티브 파일 선택 보조를 허용한다.

## 체크리스트

- 검색 결과 최소 5건 이상 분석했는가
- 가격/비용/유지비 구조를 실제 상위글 패턴 기준으로 정리했는가
- Claude 프롬프트가 상위글 복붙이 아니라 추상화된 규칙 중심인가
- 이미지 위치 계획이 본문 구조와 연결되어 있는가
- 네이버 에디터에서 최종 배치 확인까지 했는가

## 한계와 주의점

- `cmux` 만으로도 수집과 입력은 가능하지만, 네이버 에디터 업로드는 브라우저 상태에 따라 흔들릴 수 있다.
- 로그인 상태가 중요한 네이버 작업은 OpenClaw가 더 안정적일 수 있다.
- 검색 결과 구조가 바뀌면 selector 와 수집 절차를 다시 손봐야 한다.
- 이 커맨드는 완전 자동 생성기보다는 분석 주도형 반자동 파이프라인으로 보는 편이 맞다.
