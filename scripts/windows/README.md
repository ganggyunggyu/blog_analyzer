# Windows 개발환경 자동 설치 스크립트

> 아무것도 없는 Windows에서 개발환경을 자동으로 구축합니다.

## 사용법

### 1단계: Windows 기본 도구 + WSL 설치

```powershell
# PowerShell (관리자 권한)
.\1-install-wsl.ps1
```

**설치 항목:**
- Git
- VS Code
- Windows Terminal
- WSL2 + Ubuntu-22.04

> ⚠️ WSL 설치 후 **재부팅 필요**

### 2단계: WSL 개발환경 설정

```powershell
# PowerShell (재부팅 후)
.\2-setup-dev.ps1
```

**설치 항목:**
- 시스템 패키지 업데이트
- 빌드 도구 (build-essential, curl, wget, git)
- Python 빌드 의존성
- uv (Python 패키지 관리자)
- Python 3.11

## 설치 후 프로젝트 설정

```bash
# WSL 터미널에서
cd ~ && mkdir -p projects && cd projects
git clone <repository-url>
cd blog_analyzer

# 패키지 설치
uv sync
uv run playwright install chromium

# 환경변수 설정
cp .env.example .env
nano .env  # API 키 입력

# 서버 실행
uv run uvicorn api:app --reload --host 0.0.0.0 --port 8000
```

## 트러블슈팅

### WSL 관련

```powershell
# WSL 재시작
wsl --shutdown
wsl

# 배포판 재설치
wsl --unregister Ubuntu-22.04
wsl --install -d Ubuntu-22.04
```

### uv 관련

```bash
# uv 재설치
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc

# 가상환경 재생성
rm -rf .venv
uv sync
```

## 요구사항

- Windows 10 (빌드 19041 이상) 또는 Windows 11
- 관리자 권한
- 인터넷 연결
