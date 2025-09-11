from __future__ import annotations

import sys
import time
import threading
import uuid
from contextlib import contextmanager
from typing import Dict, Set


class ThreadSafeProgressManager:
    """병렬 progress 요청들을 관리하는 전역 매니저"""
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._active_progresses: Dict[str, 'ProgressPrinter'] = {}
        self._output_lock = threading.Lock()
        self._line_assignments: Dict[str, int] = {}
        self._next_line = 0
        self._label_groups: Dict[str, Set[str]] = {}  # 동일 라벨의 progress ID들
        self._last_output_time: Dict[str, float] = {}  # 마지막 출력 시간 추적
        
    def register_progress(self, progress_id: str, progress: 'ProgressPrinter') -> int:
        """새 progress를 등록하고 라인 번호 할당"""
        with self._output_lock:
            self._active_progresses[progress_id] = progress
            
            # 라벨 그룹핑 - 동일 라벨끼리 묶기
            label = progress.label
            if label not in self._label_groups:
                self._label_groups[label] = set()
            self._label_groups[label].add(progress_id)
            
            line_num = self._next_line
            self._line_assignments[progress_id] = line_num
            self._next_line += 1
            return line_num
    
    def unregister_progress(self, progress_id: str) -> None:
        """progress 등록 해제"""
        with self._output_lock:
            # progress 제거
            progress = self._active_progresses.pop(progress_id, None)
            self._line_assignments.pop(progress_id, None)
            
            # 라벨 그룹에서도 제거
            if progress:
                label = progress.label
                if label in self._label_groups:
                    self._label_groups[label].discard(progress_id)
                    if not self._label_groups[label]:  # 빈 그룹이면 삭제
                        del self._label_groups[label]
                        self._last_output_time.pop(label, None)
    
    def safe_write(self, progress_id: str, message: str) -> None:
        """Thread-safe 출력 - 동일 라벨은 하나만 출력"""
        with self._output_lock:
            if progress_id not in self._line_assignments:
                print(message)
                return
                
            progress = self._active_progresses.get(progress_id)
            if not progress:
                return
                
            label = progress.label
            current_time = time.time()
            
            # 동일 라벨의 다른 progress가 최근에 출력했는지 확인
            if label in self._last_output_time:
                # 1.5초 내에 같은 라벨로 출력된 적이 있으면 스킵
                if current_time - self._last_output_time[label] < 1.5:
                    return
            
            # 동일 라벨 그룹에서 가장 먼저 등록된 progress만 출력
            label_group = self._label_groups.get(label, set())
            if label_group and min(label_group) == progress_id:
                short_id = progress_id[:6]
                print(f"[{short_id}] {message}")
                self._last_output_time[label] = current_time


class ProgressPrinter:
    def __init__(self, label: str = "Generating", width: int = 24, interval: float = 2.0):
        self.label = label
        self.width = max(8, int(width))
        self.interval = max(0.05, float(interval))
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._start_ts = 0.0
        self._pos = 0
        self._progress_id = str(uuid.uuid4())
        self._manager = ThreadSafeProgressManager()

    def start(self) -> None:
        self._start_ts = time.time()
        self._manager.register_progress(self._progress_id, self)
        self._thread.start()

    def _run(self) -> None:
        while not self._stop.is_set():
            elapsed = time.time() - self._start_ts
            filled = int(self._pos % self.width)
            bar = "#" * filled + "-" * (self.width - filled)
            message = f"[PROG] {self.label} | {bar} | {elapsed:5.1f}s"
            self._manager.safe_write(self._progress_id, message)
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
        self._manager.safe_write(self._progress_id, msg)
        self._manager.unregister_progress(self._progress_id)


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
    shortened_label = _shorten_label(label)
    pp = ProgressPrinter(label=shortened_label, width=width, interval=interval)
    pp.start()
    try:
        yield pp
    finally:
        pp.stop()

