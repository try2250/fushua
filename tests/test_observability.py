"""可观察性基础测试"""
import os
import pytest
from app.core.observability import init_sentry, init_structlog


def test_init_sentry_with_empty_dsn_is_noop(monkeypatch):
    monkeypatch.delenv("SENTRY_DSN", raising=False)
    init_sentry()  # 不应抛异常


def test_init_structlog_returns_usable_logger():
    init_structlog()
    import structlog
    logger = structlog.get_logger("test")
    logger.info("hello", key="value")  # 不应抛异常
