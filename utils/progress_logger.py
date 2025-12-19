"""진행 상황 로거 - Rich 기반 spinner"""

from __future__ import annotations

import time
from contextlib import contextmanager
from utils.logger import console


class ProgressPrinter:
    """Rich spinner 기반 프로그래스 프린터"""

    def __init__(self, label: str = "처리 중..."):
        self.label = label
        self._start_ts = 0.0
        self._status = None

    def start(self) -> None:
        self._start_ts = time.time()
        self._status = console.status(f"[bold cyan]{self.label}[/bold cyan]", spinner="dots")
        self._status.start()

    def stop(self) -> None:
        if self._status:
            self._status.stop()
        elapsed = time.time() - self._start_ts
        console.print(f"  [dim]완료 ({elapsed:.1f}s)[/dim]")


@contextmanager
def progress(label: str):
    """프로그래스 컨텍스트 매니저 - spinner 표시"""
    pp = ProgressPrinter(label=label)
    pp.start()
    try:
        yield pp
    finally:
        pp.stop()
