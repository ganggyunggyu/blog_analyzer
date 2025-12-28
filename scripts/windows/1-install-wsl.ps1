# ============================================
# 1단계: Windows 기본 도구 + WSL 설치
# ============================================
# 실행: PowerShell (관리자) → .\1-install-wsl.ps1
# 재부팅 후 → 2-setup-dev.ps1 실행

$ErrorActionPreference = "Stop"

function Write-Step { param($msg) Write-Host "`n[*] $msg" -ForegroundColor Cyan }
function Write-Success { param($msg) Write-Host "[+] $msg" -ForegroundColor Green }
function Write-Warn { param($msg) Write-Host "[!] $msg" -ForegroundColor Yellow }

# 관리자 권한 확인
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "[-] 관리자 권한이 필요합니다!" -ForegroundColor Red
    Write-Host "    PowerShell을 '관리자 권한으로 실행'해주세요." -ForegroundColor Yellow
    exit 1
}

Write-Host @"

  ____  _               _                _
 | __ )| | ___   __ _  / \   _ __   __ _| |_   _ _______ _ __
 |  _ \| |/ _ \ / _` |/ _ \ | '_ \ / _` | | | | |_  / _ \ '__|
 | |_) | | (_) | (_| / ___ \| | | | (_| | | |_| |/ /  __/ |
 |____/|_|\___/ \__, /_/   \_\_| |_|\__,_|_|\__, /___\___|_|
                |___/                       |___/

  [1/2] Windows + WSL 설치

"@ -ForegroundColor Magenta

# ========== winget 확인 ==========
Write-Step "winget 확인"
try {
    $v = winget --version
    Write-Success "winget: $v"
} catch {
    Write-Host "[-] winget이 없습니다. Microsoft Store에서 '앱 설치 관리자' 설치 필요" -ForegroundColor Red
    exit 1
}

# ========== Git ==========
Write-Step "Git 설치"
if (Get-Command git -ErrorAction SilentlyContinue) {
    Write-Success "Git 이미 설치됨: $(git --version)"
} else {
    winget install Git.Git -e --accept-source-agreements --accept-package-agreements
    Write-Success "Git 설치 완료"
}

# ========== VS Code ==========
Write-Step "VS Code 설치"
if (Get-Command code -ErrorAction SilentlyContinue) {
    Write-Success "VS Code 이미 설치됨"
} else {
    winget install Microsoft.VisualStudioCode -e --accept-source-agreements --accept-package-agreements
    Write-Success "VS Code 설치 완료"
}

# ========== Windows Terminal ==========
Write-Step "Windows Terminal 설치"
if (Get-Command wt -ErrorAction SilentlyContinue) {
    Write-Success "Windows Terminal 이미 설치됨"
} else {
    winget install Microsoft.WindowsTerminal -e --accept-source-agreements --accept-package-agreements
    Write-Success "Windows Terminal 설치 완료"
}

# ========== WSL ==========
Write-Step "WSL 확인"
$wslReady = $false
try {
    $list = wsl --list --quiet 2>$null
    if ($list -match "Ubuntu") {
        $wslReady = $true
        Write-Success "WSL + Ubuntu 이미 설치됨"
    }
} catch {}

if (-not $wslReady) {
    Write-Step "WSL + Ubuntu-22.04 설치"
    wsl --install -d Ubuntu-22.04

    Write-Host ""
    Write-Warn "============================================"
    Write-Warn "  WSL 설치 완료! 재부팅이 필요합니다."
    Write-Warn "============================================"
    Write-Host ""
    Write-Host "재부팅 후:" -ForegroundColor Yellow
    Write-Host "  1. Ubuntu 터미널이 자동으로 열립니다" -ForegroundColor White
    Write-Host "  2. 사용자 이름/비밀번호를 설정하세요" -ForegroundColor White
    Write-Host "  3. 설정 완료 후 2-setup-dev.ps1 실행" -ForegroundColor White
    Write-Host ""

    $answer = Read-Host "지금 재부팅할까요? (Y/N)"
    if ($answer -eq "Y" -or $answer -eq "y") {
        Restart-Computer -Force
    }
} else {
    Write-Host ""
    Write-Success "============================================"
    Write-Success "  1단계 완료! 다음 단계로 진행하세요."
    Write-Success "============================================"
    Write-Host ""
    Write-Host "다음: .\2-setup-dev.ps1" -ForegroundColor Yellow
}
