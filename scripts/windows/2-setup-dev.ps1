# ============================================
# 2단계: WSL 개발환경 설정
# ============================================
# 실행: PowerShell → .\2-setup-dev.ps1
# (1-install-wsl.ps1 실행 + 재부팅 후)

$ErrorActionPreference = "Stop"

Write-Host @"

  ____  _               _                _
 | __ )| | ___   __ _  / \   _ __   __ _| |_   _ _______ _ __
 |  _ \| |/ _ \ / _` |/ _ \ | '_ \ / _` | | | | |_  / _ \ '__|
 | |_) | | (_) | (_| / ___ \| | | | (_| | | |_| |/ /  __/ |
 |____/|_|\___/ \__, /_/   \_\_| |_|\__,_|_|\__, /___\___|_|
                |___/                       |___/

  [2/2] WSL 개발환경 설정

"@ -ForegroundColor Magenta

# WSL 확인
Write-Host "[*] WSL 상태 확인..." -ForegroundColor Cyan
try {
    $wslList = wsl --list --quiet 2>$null
    if (-not ($wslList -match "Ubuntu")) {
        Write-Host "[-] Ubuntu가 설치되어 있지 않습니다." -ForegroundColor Red
        Write-Host "    먼저 1-install-wsl.ps1을 실행하세요." -ForegroundColor Yellow
        exit 1
    }
    Write-Host "[+] Ubuntu 확인됨" -ForegroundColor Green
} catch {
    Write-Host "[-] WSL을 확인할 수 없습니다." -ForegroundColor Red
    exit 1
}

# WSL 내부 스크립트 생성
$wslScript = @'
#!/bin/bash
set -e

GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

step() { echo -e "\n${CYAN}[*] $1${NC}"; }
success() { echo -e "${GREEN}[+] $1${NC}"; }
warn() { echo -e "${YELLOW}[!] $1${NC}"; }

echo ""
echo "============================================"
echo "  WSL 개발환경 설정 시작"
echo "============================================"
echo ""

# 시스템 업데이트
step "시스템 패키지 업데이트"
sudo apt update && sudo apt upgrade -y
success "업데이트 완료"

# 빌드 도구 설치
step "빌드 도구 설치"
sudo apt install -y build-essential curl wget git
success "빌드 도구 설치 완료"

# Python 빌드 의존성
step "Python 빌드 의존성 설치"
sudo apt install -y libssl-dev zlib1g-dev libbz2-dev \
    libreadline-dev libsqlite3-dev libncursesw5-dev \
    xz-utils tk-dev libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev
success "Python 의존성 설치 완료"

# uv 설치
step "uv 설치 (Python 패키지 관리자)"
if command -v uv &> /dev/null; then
    success "uv 이미 설치됨: $(uv --version)"
else
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
    success "uv 설치 완료"
fi

# Python 설치
step "Python 3.11 설치"
source ~/.bashrc 2>/dev/null || true
export PATH="$HOME/.local/bin:$PATH"
uv python install 3.11
success "Python 3.11 설치 완료"

# 설치 확인
echo ""
echo "============================================"
echo "  설치 완료!"
echo "============================================"
echo ""
echo -e "${GREEN}설치된 도구:${NC}"
echo "  - git: $(git --version 2>/dev/null || echo 'N/A')"
echo "  - uv: $(uv --version 2>/dev/null || echo 'N/A')"
echo "  - python: $(uv python list 2>/dev/null | head -1 || echo 'N/A')"
echo ""
echo -e "${YELLOW}다음 단계:${NC}"
echo "  1. 터미널 재시작 (exit 후 다시 wsl)"
echo "  2. 프로젝트 클론:"
echo "     cd ~ && mkdir -p projects && cd projects"
echo "     git clone <repository-url>"
echo "     cd blog_analyzer"
echo ""
echo "  3. 프로젝트 설정:"
echo "     uv sync"
echo "     uv run playwright install chromium"
echo "     cp .env.example .env"
echo "     nano .env  # API 키 입력"
echo ""
echo "  4. 서버 실행:"
echo "     uv run uvicorn api:app --reload --host 0.0.0.0 --port 8000"
echo ""
'@

# WSL에서 스크립트 실행
Write-Host "`n[*] WSL 개발환경 설정 시작..." -ForegroundColor Cyan
Write-Host "    (sudo 비밀번호 입력이 필요할 수 있습니다)`n" -ForegroundColor Yellow

# 임시 스크립트 파일 생성
$tempScript = [System.IO.Path]::GetTempFileName()
$wslScript | Out-File -FilePath $tempScript -Encoding utf8

# WSL 경로로 변환
$wslPath = wsl wslpath -u $tempScript.Replace('\', '/')

# WSL에서 실행
wsl bash $wslPath

# 임시 파일 삭제
Remove-Item $tempScript -ErrorAction SilentlyContinue

Write-Host "`n[+] 2단계 완료!" -ForegroundColor Green
Write-Host "    터미널을 재시작하고 프로젝트를 설정하세요.`n" -ForegroundColor Yellow
