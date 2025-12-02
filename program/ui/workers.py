"""백그라운드 워커 스레드"""
from __future__ import annotations

from PySide6.QtCore import QThread, Signal

from program.core import Generator

__all__ = ["BatchGenerateWorker"]


class BatchGenerateWorker(QThread):
    """일괄 생성 워커"""

    item_started = Signal(int)
    item_finished = Signal(int, str, str)
    item_error = Signal(int, str)
    all_finished = Signal()

    def __init__(self, engine: str, keywords: list[str], ref: str):
        super().__init__()
        self.engine = engine
        self.keywords = keywords
        self.ref = ref
        self._stop_requested = False

    def stop(self) -> None:
        self._stop_requested = True

    def run(self) -> None:
        for idx, keyword in enumerate(self.keywords):
            if self._stop_requested:
                break

            self.item_started.emit(idx)

            try:
                result, category = Generator.generate(
                    engine=self.engine,
                    keyword=keyword,
                    ref=self.ref,
                )
                self.item_finished.emit(idx, result, category)
            except Exception as e:
                self.item_error.emit(idx, str(e))

        self.all_finished.emit()
