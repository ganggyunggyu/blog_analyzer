from __future__ import annotations

import sys
import time
import threading
from contextlib import contextmanager


class ProgressPrinter:
    def __init__(self, label: str = "Generating", width: int = 24, interval: float = 0.2):
        self.label = label
        self.width = max(8, int(width))
        self.interval = max(0.05, float(interval))
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._start_ts = 0.0
        self._pos = 0

    def start(self) -> None:
        self._start_ts = time.time()
        sys.stdout.write("\n")
        sys.stdout.flush()
        self._thread.start()

    def _run(self) -> None:
        while not self._stop.is_set():
            elapsed = time.time() - self._start_ts
            filled = int(self._pos % self.width)
            bar = "#" * filled + "-" * (self.width - filled)
            sys.stdout.write(f"\r[PROG] {self.label} | {bar} | {elapsed:5.1f}s")
            sys.stdout.flush()
            self._pos += 1
            time.sleep(self.interval)

    def stop(self, final_message: str | None = None) -> None:
        self._stop.set()
        try:
            self._thread.join(timeout=0.5)
        except Exception:
            pass
        elapsed = time.time() - self._start_ts
        msg = final_message or f"[PROG] {self.label} | done in {elapsed:.2f}s"
        sys.stdout.write(f"\r{msg}\n")
        sys.stdout.flush()


@contextmanager
def progress(label: str, width: int = 24, interval: float = 0.2):
    pp = ProgressPrinter(label=label, width=width, interval=interval)
    pp.start()
    try:
        yield pp
    finally:
        pp.stop()

