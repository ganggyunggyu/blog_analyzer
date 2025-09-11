from __future__ import annotations

import time
from contextlib import contextmanager


class ProgressPrinter:
    """간소화된 프로그래스 프린터 - 바 제거하고 시작/완료 메시지만 출력"""
    
    def __init__(self, label: str = "Generating", width: int = 24, interval: float = 2.0):
        self.label = label
        self._start_ts = 0.0

    def start(self) -> None:
        self._start_ts = time.time()
        print(f"[START] {self.label}")

    def stop(self, final_message: str | None = None) -> None:
        elapsed = time.time() - self._start_ts
        msg = final_message or f"[DONE] {self.label} | completed in {elapsed:.2f}s"
        print(msg)


def _shorten_label(label: str, max_length: int = 50) -> str:
    """라벨을 적절한 길이로 줄임"""
    if len(label) <= max_length:
        return label
    
    parts = label.split(':')
    if len(parts) == 3:  # service:model:keyword 형태
        service, model, keyword = parts
        # 키워드만 줄이기
        if len(keyword) > 20:
            keyword = keyword[:17] + "..."
        return f"{service}:{model}:{keyword}"
    
    # 일반적인 경우
    return label[:max_length-3] + "..." if len(label) > max_length else label


@contextmanager
def progress(label: str, width: int = 24, interval: float = 2.0):
    """간소화된 프로그래스 컨텍스트 매니저 - 시작/완료 메시지만 출력"""
    shortened_label = _shorten_label(label)
    pp = ProgressPrinter(label=shortened_label, width=width, interval=interval)
    pp.start()
    try:
        yield pp
    finally:
        pp.stop()

