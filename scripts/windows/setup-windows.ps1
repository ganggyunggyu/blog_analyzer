# Blog Analyzer - Windows 개발환경 설정 스크립트
# 관리자 권한으로 실행 필요: PowerShell (관리자)

param(
    [switch]$SkipReboot,
    [switch]$Phase2
)

$ErrorActionPreference = "Stop"

# 색상 출력 함수
function Write-Step { param($msg) Write-Host "`n[*] $msg" -ForegroundColor Cyan }
function Write-Success { param($msg) Write-Host "[+] $msg" -ForegroundColor Green }
function Write-Warning { param($msg) Write-Host "[!] $msg" -ForegroundColor Yellow }
function Write-Error { param($msg) Write-Host "[-] $msg" -ForegroundColor Red }

# 관리자 권한 확인
function Test-Admin {
    $currentUser = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
    return $currentUser.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

if (-not (Test-Admin)) {
    Write-Error "관리자 권한이 필요합니다!"
    Write-Host "PowerShell을 관리자 권한으로 다시 실행해주세요." -ForegroundColor Yellow
    exit 1
}

Write-Host @"

 ____  _             _____           _
| __ )| | ___   __ _|  ___|_ _  ___| |_ ___  _ __ _   _
|  _ \| |/ _ \ / _` | |_ / _` |/ __| __/ _ \| '__| | | |
| |_) | | (_) | (_| |  _| (_| | (__| || (_) | |  | |_| |
|____/|_|\___/ \__, |_|  \__,_|\___|\__\___/|_|   \__, |
               |___/                              |___/

  Windows Development Environment Setup

"@ -ForegroundColor Magenta

# ========== Phase 1: Windows 기본 설정 ==========
if (-not $Phase2) {
    Write-Step "Phase 1: Windows 기본 도구 설치"

    # winget 확인
    Write-Step "winget 확인 중..."
    try {
        $wingetVersion = winget --version
        Write-Success "winget 설치됨: $wingetVersion"
    } catch {
        Write-Error "winget이 설치되어 있지 않습니다."
        Write-Host "Microsoft Store에서 '앱 설치 관리자'를 설치해주세요." -ForegroundColor Yellow
        exit 1
    }

    # Git 설치
    Write-Step "Git 설치 중..."
    $gitInstalled = Get-Command git -ErrorAction SilentlyContinue
    if ($gitInstalled) {
        Write-Success "Git 이미 설치됨: $(git --version)"
    } else {
        winget install Git.Git -e --accept-source-agreements --accept-package-agreements
        Write-Success "Git 설치 완료"
    }

    # VS Code 설치
    Write-Step "VS Code 설치 중..."
    $codeInstalled = Get-Command code -ErrorAction SilentlyContinue
    if ($codeInstalled) {
        Write-Success "VS Code 이미 설치됨"
    } else {
        winget install Microsoft.VisualStudioCode -e --accept-source-agreements --accept-package-agreements
        Write-Success "VS Code 설치 완료"
    }

    # Windows Terminal 설치
    Write-Step "Windows Terminal 설치 중..."
    $wtInstalled = Get-Command wt -ErrorAction SilentlyContinue
    if ($wtInstalled) {
        Write-Success "Windows Terminal 이미 설치됨"
    } else {
        winget install Microsoft.WindowsTerminal -e --accept-source-agreements --accept-package-agreements
        Write-Success "Windows Terminal 설치 완료"
    }

    # WSL 설치 확인
    Write-Step "WSL 확인 중..."
    $wslInstalled = $false
    try {
        $wslList = wsl --list --quiet 2>$null
        if ($wslList -match "Ubuntu") {
            $wslInstalled = $true
            Write-Success "WSL + Ubuntu 이미 설치됨"
        }
    } catch {}

    if (-not $wslInstalled) {
        Write-Step "WSL + Ubuntu 설치 중..."
        wsl --install -d Ubuntu-22.04

        Write-Host ""
        Write-Warning "WSL 설치를 완료하려면 재부팅이 필요합니다!"
        Write-Host ""

        if (-not $SkipReboot) {
            Write-Host "재부팅 후 자동으로 Phase 2가 실행됩니다." -ForegroundColor Yellow

            # 재부팅 후 자동 실행 등록
            $scriptPath = $MyInvocation.MyCommand.Path
            $taskAction = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-ExecutionPolicy Bypass -File `"$scriptPath`" -Phase2"
            $taskTrigger = New-ScheduledTaskTrigger -AtLogOn
            $taskSettings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries

            Register-ScheduledTask -TaskName "BlogAnalyzer_Setup_Phase2" -Action $taskAction -Trigger $taskTrigger -Settings $taskSettings -Force | Out-Null
            Write-Success "Phase 2 자동 실행 등록 완료"

            Write-Host ""
            Write-Host "5초 후 재부팅됩니다... (Ctrl+C로 취소)" -ForegroundColor Red
            Start-Sleep -Seconds 5
            Restart-Computer -Force
        } else {
            Write-Host ""
            Write-Host "재부팅 후 다음 명령어를 실행하세요:" -ForegroundColor Yellow
            Write-Host "  .\setup-windows.ps1 -Phase2" -ForegroundColor White
        }
        exit 0
    }

    # WSL이 이미 설치되어 있으면 Phase 2로 진행
    Write-Host ""
    Write-Success "Phase 1 완료! Phase 2로 진행합니다..."
    $Phase2 = $true
}

# ========== Phase 2: WSL 내 환경 설정 ==========
if ($Phase2) {
    Write-Step "Phase 2: WSL 환경 설정"

    # 예약된 태스크 삭제
    Unregister-ScheduledTask -TaskName "BlogAnalyzer_Setup_Phase2" -Confirm:$false -ErrorAction SilentlyContinue

    # Ubuntu 실행 확인
    Write-Step "Ubuntu 확인 중..."
    try {
        $ubuntuCheck = wsl -d Ubuntu-22.04 -- echo "ok" 2>$null
        if ($ubuntuCheck -ne "ok") {
            throw "Ubuntu not ready"
        }
        Write-Success "Ubuntu 준비됨"
    } catch {
        Write-Warning "Ubuntu 초기 설정이 필요합니다."
        Write-Host "Ubuntu 터미널에서 사용자 이름/비밀번호를 설정한 후 다시 실행해주세요." -ForegroundColor Yellow
        wsl -d Ubuntu-22.04
        exit 0
    }

    # WSL 내 setup 스크립트 복사 및 실행
    Write-Step "WSL 환경 설정 스크립트 실행 중..."

    $wslScript = @'
#!/bin/bash
set -e

GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${CYAN}[*] 시스템 업데이트 중...${NC}"
sudo apt update && sudo apt upgrade -y

echo -e "${CYAN}[*] 빌드 도구 설치 중...${NC}"
sudo apt install -y build-essential curl wget git \
    libssl-dev zlib1g-dev libbz2-dev libreadline-dev \
    libsqlite3-dev libncursesw5-dev xz-utils tk-dev \
    libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev

echo -e "${CYAN}[*] uv 설치 중...${NC}"
if command -v uv &> /dev/null; then
    echo -e "${GREEN}[+] uv 이미 설치됨${NC}"
else
    curl -LsSf https://astral.sh/uv/install.sh | sh
    source ~/.bashrc
fi

echo -e "${CYAN}[*] Python 3.11 설치 중...${NC}"
~/.local/bin/uv python install 3.11 || true

echo -e "${GREEN}[+] WSL 환경 설정 완료!${NC}"
echo ""
echo -e "${YELLOW}다음 단계:${NC}"
echo "  1. cd ~/projects"
echo "  2. git clone <your-repo> blog_analyzer"
echo "  3. cd blog_analyzer"
echo "  4. uv sync"
echo "  5. cp .env.example .env && nano .env"
echo "  6. uv run playwright install chromium"
echo "  7. uv run uvicorn api:app --reload"
'@

    # WSL에서 스크립트 실행
    $wslScript | wsl -d Ubuntu-22.04 -- bash

    Write-Host ""
    Write-Success "============================================"
    Write-Success "  모든 설치가 완료되었습니다!"
    Write-Success "============================================"
    Write-Host ""
    Write-Host "다음 단계:" -ForegroundColor Yellow
    Write-Host "  1. Windows Terminal 실행" -ForegroundColor White
    Write-Host "  2. Ubuntu 탭 선택" -ForegroundColor White
    Write-Host "  3. 프로젝트 클론:" -ForegroundColor White
    Write-Host "     mkdir -p ~/projects && cd ~/projects" -ForegroundColor Gray
    Write-Host "     git clone <your-repo> blog_analyzer" -ForegroundColor Gray
    Write-Host "     cd blog_analyzer && uv sync" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  4. VS Code에서 열기:" -ForegroundColor White
    Write-Host "     code ." -ForegroundColor Gray
    Write-Host ""
}
