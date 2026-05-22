import pytest
from fastapi.testclient import TestClient
from app.main import app


def test_request_logging_records_duration(caplog):
    """测试请求日志记录耗时"""
    client = TestClient(app)

    with caplog.at_level("INFO"):
        response = client.get("/health")

    assert response.status_code == 200
    # 验证日志包含请求信息
    log_records = [r for r in caplog.records if "GET /health" in r.message]
    assert len(log_records) > 0
    # 验证包含耗时信息
    assert "duration_ms" in log_records[0].message or "ms" in log_records[0].message
