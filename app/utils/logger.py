import logging
from typing import Optional, Any, Dict
from datetime import datetime
from fastapi import Request

logger = logging.getLogger("fushua")


class SensitiveDataFilter:
    """敏感信息过滤器，自动脱敏密码、token等字段"""

    SENSITIVE_KEYS = {
        "password", "password_hash", "token", "secret", "api_key",
        "access_token", "refresh_token", "authorization", "cookie",
        "session", "csrf_token"
    }

    @classmethod
    def filter(cls, data: Any) -> Any:
        """递归过滤敏感信息"""
        if isinstance(data, dict):
            return {k: cls._filter_value(k, v) for k, v in data.items()}
        elif isinstance(data, list):
            return [cls.filter(item) for item in data]
        return data

    @classmethod
    def _filter_value(cls, key: str, value: Any) -> Any:
        """过滤单个值"""
        if isinstance(key, str) and key.lower() in cls.SENSITIVE_KEYS:
            return "***"
        if isinstance(value, dict):
            return cls.filter(value)
        elif isinstance(value, list):
            return [cls.filter(item) for item in value]
        return value


class AppLogger:
    """应用日志工具，提供结构化日志记录"""

    @staticmethod
    def _format_message(
        level: str,
        message: str,
        request_id: Optional[str] = None,
        user_id: Optional[int] = None,
        path: Optional[str] = None,
        extra: Optional[Dict[str, Any]] = None
    ) -> str:
        """格式化日志消息"""
        parts = [f"[{level}]", "fushua"]

        if request_id:
            parts.append(f"[req:{request_id[:8]}]")
        if user_id:
            parts.append(f"[user:{user_id}]")
        if path:
            parts.append(f"[path:{path}]")

        parts.append(message)

        if extra:
            filtered_extra = SensitiveDataFilter.filter(extra)
            parts.append(f"| {filtered_extra}")

        return " ".join(parts)

    @staticmethod
    def _extract_context(request: Optional[Request] = None) -> tuple:
        """从请求中提取上下文信息"""
        if not request:
            return None, None, None

        request_id = getattr(request.state, "request_id", None)
        user_id = getattr(request.state, "user_id", None)
        path = request.url.path if hasattr(request, "url") else None

        return request_id, user_id, path

    @classmethod
    def info(
        cls,
        message: str,
        request: Optional[Request] = None,
        extra: Optional[Dict[str, Any]] = None
    ):
        """记录 INFO 级别日志"""
        request_id, user_id, path = cls._extract_context(request)
        formatted = cls._format_message("INFO", message, request_id, user_id, path, extra)
        logger.info(formatted)

    @classmethod
    def warning(
        cls,
        message: str,
        request: Optional[Request] = None,
        extra: Optional[Dict[str, Any]] = None
    ):
        """记录 WARNING 级别日志"""
        request_id, user_id, path = cls._extract_context(request)
        formatted = cls._format_message("WARNING", message, request_id, user_id, path, extra)
        logger.warning(formatted)

    @classmethod
    def error(
        cls,
        message: str,
        request: Optional[Request] = None,
        extra: Optional[Dict[str, Any]] = None,
        exc_info: bool = False
    ):
        """记录 ERROR 级别日志"""
        request_id, user_id, path = cls._extract_context(request)
        formatted = cls._format_message("ERROR", message, request_id, user_id, path, extra)
        logger.error(formatted, exc_info=exc_info)

    @classmethod
    def debug(
        cls,
        message: str,
        request: Optional[Request] = None,
        extra: Optional[Dict[str, Any]] = None
    ):
        """记录 DEBUG 级别日志"""
        request_id, user_id, path = cls._extract_context(request)
        formatted = cls._format_message("DEBUG", message, request_id, user_id, path, extra)
        logger.debug(formatted)


# 便捷函数
def log_info(message: str, request: Optional[Request] = None, **kwargs):
    """记录 INFO 日志的便捷函数"""
    AppLogger.info(message, request, extra=kwargs if kwargs else None)


def log_warning(message: str, request: Optional[Request] = None, **kwargs):
    """记录 WARNING 日志的便捷函数"""
    AppLogger.warning(message, request, extra=kwargs if kwargs else None)


def log_error(message: str, request: Optional[Request] = None, exc_info: bool = False, **kwargs):
    """记录 ERROR 日志的便捷函数"""
    AppLogger.error(message, request, extra=kwargs if kwargs else None, exc_info=exc_info)


def log_debug(message: str, request: Optional[Request] = None, **kwargs):
    """记录 DEBUG 日志的便捷函数"""
    AppLogger.debug(message, request, extra=kwargs if kwargs else None)
