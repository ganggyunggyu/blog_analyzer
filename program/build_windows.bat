@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion

REM Blog Analyzer - Windows 빌드 스크립트

echo === Blog Analyzer Windows Build ===

set SCRIPT_DIR=%~dp0
set PROJECT_ROOT=%SCRIPT_DIR%..
cd /d "%PROJECT_ROOT%"

echo Project root: %PROJECT_ROOT%

REM PyInstaller 설치 확인
pip show pyinstaller > nul 2>&1
if errorlevel 1 (
    echo PyInstaller 설치 중...
    pip install pyinstaller
)

REM 기존 빌드 정리
if exist "%PROJECT_ROOT%\dist\BlogAnalyzer" rmdir /s /q "%PROJECT_ROOT%\dist\BlogAnalyzer"
if exist "%PROJECT_ROOT%\build" rmdir /s /q "%PROJECT_ROOT%\build"

REM PyInstaller 실행
echo 빌드 시작...
pyinstaller ^
    --name "BlogAnalyzer" ^
    --windowed ^
    --onedir ^
    --noconfirm ^
    --clean ^
    --add-data "_prompts;_prompts" ^
    --add-data "_constants;_constants" ^
    --add-data "llm;llm" ^
    --add-data "utils;utils" ^
    --add-data "analyzer;analyzer" ^
    --add-data "ai_lib;ai_lib" ^
    --add-data "schema;schema" ^
    --add-data ".env;." ^
    --hidden-import "PySide6.QtCore" ^
    --hidden-import "PySide6.QtGui" ^
    --hidden-import "PySide6.QtWidgets" ^
    --hidden-import "anthropic" ^
    --hidden-import "openai" ^
    --hidden-import "google.genai" ^
    --hidden-import "xai_sdk" ^
    --hidden-import "pymongo" ^
    --hidden-import "dotenv" ^
    --collect-all "PySide6" ^
    --distpath "%PROJECT_ROOT%\dist" ^
    --workpath "%PROJECT_ROOT%\build" ^
    --specpath "%PROJECT_ROOT%\build" ^
    "%PROJECT_ROOT%\program\main.py"

echo.
echo === 빌드 완료 ===
echo 앱 위치: %PROJECT_ROOT%\dist\BlogAnalyzer\BlogAnalyzer.exe
echo.
echo 실행: dist\BlogAnalyzer\BlogAnalyzer.exe

pause
