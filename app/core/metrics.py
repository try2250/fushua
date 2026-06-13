"""进程内简易 metrics 计数器（5 分钟滚动窗口）。"""
import time
import threading
from collections import deque


_WINDOW_SECONDS = 300


class _RollingCounter:
    def __init__(self):
        self._events = deque()
        self._lock = threading.Lock()

    def record(self):
        with self._lock:
            now = time.time()
            self._events.append(now)
            self._gc(now)

    def count(self) -> int:
        with self._lock:
            self._gc(time.time())
            return len(self._events)

    def _gc(self, now: float):
        cutoff = now - _WINDOW_SECONDS
        while self._events and self._events[0] < cutoff:
            self._events.popleft()


request_counter = _RollingCounter()
error_counter = _RollingCounter()
