"""21Lab 로깅 유틸리티

rich 기반의 예쁜 콘솔 출력을 제공합니다.

Usage:
    from utils.logger import console, log

    log.info("서버 시작")
    log.success("원고 생성 완료", keyword="리쥬란", length=2847)
    log.warning("길이 부족")
    log.error("API 오류")

    log.step(1, 4, "프롬프트 로딩")
    log.step(2, 4, "API 호출")

    log.header("원고 생성")
    log.divider()

    log.kv("키워드", "리쥬란")
    log.kv("길이", 2847)
"""

from __future__ import annotations
from datetime import datetime
from typing import Any, Optional

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeElapsedColumn
from rich.panel import Panel
from rich.table import Table

console = Console()

# 긴 텍스트 함축 설정
MAX_DISPLAY_LENGTH = 30


def truncate(text: str, max_len: int = MAX_DISPLAY_LENGTH) -> str:
    """긴 텍스트를 함축해서 표시"""
    if not text:
        return ""
    text = str(text).replace("\n", " ").strip()
    if len(text) <= max_len:
        return text
    return text[:max_len - 3] + "..."


class Logger:
    """21Lab 로거"""

    def __init__(self):
        self.console = console

    def _timestamp(self) -> str:
        return datetime.now().strftime("%H:%M:%S")

    def info(self, msg: str, **kwargs):
        """정보 로그"""
        extra = self._format_kwargs(kwargs)
        self.console.print(f"[dim]{self._timestamp()}[/dim] [blue]INFO[/blue]     {msg}{extra}")

    def success(self, msg: str, **kwargs):
        """성공 로그"""
        extra = self._format_kwargs(kwargs)
        self.console.print(f"[dim]{self._timestamp()}[/dim] [green]SUCCESS[/green]  ✨ {msg}{extra}")

    def warning(self, msg: str, **kwargs):
        """경고 로그"""
        extra = self._format_kwargs(kwargs)
        self.console.print(f"[dim]{self._timestamp()}[/dim] [yellow]WARNING[/yellow]  ⚠️  {msg}{extra}")

    def error(self, msg: str, **kwargs):
        """에러 로그"""
        extra = self._format_kwargs(kwargs)
        self.console.print(f"[dim]{self._timestamp()}[/dim] [red]ERROR[/red]    ❌ {msg}{extra}")

    def debug(self, msg: str, **kwargs):
        """디버그 로그"""
        extra = self._format_kwargs(kwargs)
        self.console.print(f"[dim]{self._timestamp()}[/dim] [dim]DEBUG[/dim]    {msg}{extra}")

    def step(self, current: int, total: int, msg: str, emoji: str = "🔹"):
        """단계 로그 (yarn 스타일)"""
        self.console.print(f"[cyan][{current}/{total}][/cyan] {emoji} {msg}")

    def header(self, title: str, emoji: str = "📋"):
        """헤더 출력"""
        self.console.print()
        self.console.rule(f"[bold cyan]{emoji} {title}[/bold cyan]")

    def divider(self, style: str = "dim"):
        """구분선"""
        self.console.rule(style=style)

    def kv(self, key: str, value: Any, key_style: str = "cyan"):
        """키-값 출력"""
        self.console.print(f"  [{key_style}]{key}[/{key_style}]: {value}")

    def table(self, title: str, data: dict[str, Any]):
        """테이블 형태로 데이터 출력"""
        table = Table(title=title, show_header=False, box=None)
        table.add_column("Key", style="cyan")
        table.add_column("Value")
        for k, v in data.items():
            table.add_row(k, str(v))
        self.console.print(table)

    def panel(self, content: str, title: str = "", style: str = "blue"):
        """패널 출력"""
        self.console.print(Panel(content, title=title, border_style=style))

    def _format_kwargs(self, kwargs: dict) -> str:
        if not kwargs:
            return ""
        parts = [f"[dim]{k}={truncate(str(v))}[/dim]" for k, v in kwargs.items()]
        return " " + " ".join(parts)

class ProgressLogger:
    """프로그레스바 로거 - Rich 기반으로 로그와 충돌 없음"""

    def __init__(self, description: str = "처리 중...", total: int = 100):
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(bar_width=40),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            console=console,
            transient=False,
        )
        self.description = description
        self.total = total
        self.task_id = None

    def __enter__(self):
        self.progress.start()
        self.task_id = self.progress.add_task(self.description, total=self.total)
        return self

    def __exit__(self, *args):
        self.progress.stop()

    def update(self, advance: int = 1, description: str = None):
        """진행률 업데이트"""
        if description:
            self.progress.update(self.task_id, description=description)
        self.progress.update(self.task_id, advance=advance)

    def set(self, completed: int):
        """진행률 직접 설정"""
        self.progress.update(self.task_id, completed=completed)

    def log(self, msg: str, style: str = "dim"):
        """프로그레스 바 위에 로그 출력 (프로그레스 안 깨짐)"""
        self.progress.console.print(f"[{style}]{msg}[/{style}]")

    def skip(self, filename: str, reason: str = "건너뜀"):
        """파일 스킵 로그"""
        self.progress.console.print(f"  [dim]→ {filename}: {reason}[/dim]")

    def error(self, filename: str, error: str):
        """에러 로그"""
        self.progress.console.print(f"  [red]✗ {filename}: {error}[/red]")

    def success(self, filename: str, detail: str = ""):
        """성공 로그"""
        extra = f" ({detail})" if detail else ""
        self.progress.console.print(f"  [green]✓ {filename}{extra}[/green]")

# 싱글톤 인스턴스
log = Logger()

# 편의 함수들
def progress(description: str = "처리 중...", total: int = 100) -> ProgressLogger:
    """프로그레스바 생성

    Usage:
        with progress("원고 생성 중...", total=100) as p:
            for i in range(100):
                p.update()
    """
    return ProgressLogger(description, total)

# API 호출용 특화 함수들
def log_api_start(service: str, keyword: str, category: str = ""):
    """API 호출 시작 로그"""
    log.header(f"{service} 원고 생성", "🚀")
    log.kv("키워드", truncate(keyword, 40))
    if category:
        log.kv("카테고리", category)
    log.divider()

def log_api_end(service: str, length: int, length_no_space: int):
    """API 호출 완료 로그"""
    log.divider()
    log.success(f"{service} 완료", length=f"{length_no_space}자")

def log_api_error(service: str, error: Exception):
    """API 에러 로그"""
    log.error(f"{service} 실패: {error}")
