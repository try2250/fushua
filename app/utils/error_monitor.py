from datetime import datetime
from typing import Optional, List, Dict
from collections import deque
from dataclasses import dataclass, asdict
import threading


@dataclass
class ErrorEntry:
    """错误记录条目"""
    timestamp: datetime
    request_id: str
    user_id: Optional[int]
    path: str
    method: str
    error_type: str
    error_message: str
    status_code: int

    def to_dict(self) -> Dict:
        """转换为字典"""
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        return data


class ErrorMonitor:
    """错误监控器，在内存中保存最近的错误记录"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self, max_size: int = 50):
        if self._initialized:
            return
        self._errors = deque(maxlen=max_size)
        self._lock = threading.Lock()
        self._initialized = True

    def add_error(
        self,
        request_id: str,
        user_id: Optional[int],
        path: str,
        method: str,
        error_type: str,
        error_message: str,
        status_code: int = 500
    ):
        """添加错误记录"""
        entry = ErrorEntry(
            timestamp=datetime.now(),
            request_id=request_id,
            user_id=user_id,
            path=path,
            method=method,
            error_type=error_type,
            error_message=error_message,
            status_code=status_code
        )

        with self._lock:
            self._errors.append(entry)

    def get_recent_errors(self, limit: int = 20) -> List[ErrorEntry]:
        """获取最近的错误记录"""
        with self._lock:
            errors = list(self._errors)
            return errors[-limit:] if len(errors) > limit else errors

    def get_error_count(self) -> int:
        """获取当前错误总数"""
        with self._lock:
            return len(self._errors)

    def clear(self):
        """清空错误记录"""
        with self._lock:
            self._errors.clear()


# 全局单例
error_monitor = ErrorMonitor()
