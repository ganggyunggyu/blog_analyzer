#!/bin/bash

# Blog Analyzer - macOS 빌드 스크립트

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

echo "=== Blog Analyzer macOS Build ==="
echo "Project root: $PROJECT_ROOT"

# PyInstaller 설치 확인
if ! command -v pyinstaller &> /dev/null; then
    echo "PyInstaller 설치 중..."
    pip install pyinstaller
fi

# 기존 빌드 정리
rm -rf "$PROJECT_ROOT/dist/BlogAnalyzer.app"
rm -rf "$PROJECT_ROOT/build"

# PyInstaller 실행
echo "빌드 시작..."
pyinstaller \
    --name "BlogAnalyzer" \
    --windowed \
    --onedir \
    --noconfirm \
    --clean \
    --add-data "_prompts:_prompts" \
    --add-data "_constants:_constants" \
    --add-data "llm:llm" \
    --add-data "utils:utils" \
    --add-data "analyzer:analyzer" \
    --add-data "ai_lib:ai_lib" \
    --add-data "schema:schema" \
    --add-data ".env:.env" \
    --hidden-import "PySide6.QtCore" \
    --hidden-import "PySide6.QtGui" \
    --hidden-import "PySide6.QtWidgets" \
    --hidden-import "anthropic" \
    --hidden-import "openai" \
    --hidden-import "google.genai" \
    --hidden-import "xai_sdk" \
    --hidden-import "pymongo" \
    --hidden-import "dotenv" \
    --collect-all "PySide6" \
    --distpath "$PROJECT_ROOT/dist" \
    --workpath "$PROJECT_ROOT/build" \
    --specpath "$PROJECT_ROOT/build" \
    "$PROJECT_ROOT/program/main.py"

echo ""
echo "=== 빌드 완료 ==="
echo "앱 위치: $PROJECT_ROOT/dist/BlogAnalyzer.app"
echo ""
echo "실행: open dist/BlogAnalyzer.app"
