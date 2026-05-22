import pytest
from fastapi.testclient import TestClient
from fastapi import Request
from app.main import app, generic_exception_handler
from app.utils.error_monitor import error_monitor
from unittest.mock import MagicMock, Mock, PropertyMock
import asyncio
from tests.conftest import get_csrf_token


def test_global_exception_handler_logs_500_errors(caplog):
    """测试全局异常处理器记录500错误"""
    # 清空错误监控器
    error_monitor.clear()

    # 创建模拟请求（API路径，返回JSON）
    mock_request = MagicMock(spec=Request)
    mock_request.url.path = "/api/test-path"
    mock_request.method = "GET"
    mock_request.state.request_id = "test-req-123"
    mock_request.state.user_id = None

    # 创建测试异常
    test_exception = ValueError("Test error message")

    # 调用异常处理器
    with caplog.at_level("ERROR"):
        response = asyncio.run(generic_exception_handler(mock_request, test_exception))

    # 验证返回500
    assert response.status_code == 500

    # 验证错误日志
    error_logs = [r for r in caplog.records if r.levelname == "ERROR"]
    assert len(error_logs) > 0

    # 验证日志包含异常信息
    log_messages = " ".join([r.message for r in error_logs])
    assert "ValueError" in log_messages or "Test error" in log_messages

    # 验证错误被添加到监控器
    recent_errors = error_monitor.get_recent_errors()
    assert len(recent_errors) > 0
    assert recent_errors[-1].error_type == "ValueError"
    assert recent_errors[-1].error_message == "Test error message"
    assert recent_errors[-1].status_code == 500


def test_global_exception_handler_returns_json_for_api(caplog):
    """测试全局异常处理器对API路径返回JSON"""
    error_monitor.clear()

    # 创建模拟API请求
    mock_request = MagicMock(spec=Request)
    mock_request.url.path = "/api/v1/test"
    mock_request.method = "POST"
    mock_request.state.request_id = "test-req-456"
    mock_request.state.user_id = 1

    # 创建测试异常
    test_exception = RuntimeError("API test error")

    # 调用异常处理器
    with caplog.at_level("ERROR"):
        response = asyncio.run(generic_exception_handler(mock_request, test_exception))

    # 验证返回500
    assert response.status_code == 500

    # 验证返回JSON格式
    assert response.media_type == "application/json"
    # 验证JSON结构
    import json
    response_data = json.loads(response.body.decode())
    assert response_data == {"code": 10000, "message": "系统错误", "data": None}


def test_global_exception_handler_returns_html_for_web(caplog):
    """测试全局异常处理器对Web路径返回HTML"""
    error_monitor.clear()

    # 创建模拟Web请求
    mock_request = MagicMock(spec=Request)
    mock_request.url.path = "/teacher/questions"
    mock_request.method = "GET"
    mock_request.state.request_id = "test-req-789"
    mock_request.state.user_id = 2
    mock_request.app.state.templates = app.state.templates

    # 创建测试异常
    test_exception = RuntimeError("Web test error")

    # 调用异常处理器
    with caplog.at_level("ERROR"):
        response = asyncio.run(generic_exception_handler(mock_request, test_exception))

    # 验证返回500
    assert response.status_code == 500

    # 验证返回HTML格式（TemplateResponse）
    assert hasattr(response, 'body') or hasattr(response, 'template')


def test_global_exception_handler_captures_request_context(caplog):
    """测试全局异常处理器捕获请求上下文"""
    error_monitor.clear()

    # 创建模拟请求（API路径）
    mock_request = MagicMock(spec=Request)
    mock_request.url.path = "/api/student/dashboard"
    mock_request.method = "GET"
    mock_request.state.request_id = "test-req-context"
    mock_request.state.user_id = 5

    # 创建测试异常
    test_exception = Exception("Context test error")

    # 调用异常处理器
    with caplog.at_level("ERROR"):
        response = asyncio.run(generic_exception_handler(mock_request, test_exception))

    assert response.status_code == 500

    # 验证错误监控器记录了请求信息
    recent_errors = error_monitor.get_recent_errors()
    assert len(recent_errors) > 0
    last_error = recent_errors[-1]
    assert last_error.path == "/api/student/dashboard"
    assert last_error.method == "GET"
    assert last_error.request_id == "test-req-context"
    assert last_error.user_id == 5


def test_global_exception_handler_uses_exc_info(caplog):
    """测试全局异常处理器使用exc_info记录完整堆栈"""
    error_monitor.clear()

    # 创建模拟请求（API路径）
    mock_request = MagicMock(spec=Request)
    mock_request.url.path = "/api/test"
    mock_request.method = "GET"
    mock_request.state.request_id = "test-req-stack"
    mock_request.state.user_id = None

    # 创建测试异常
    test_exception = RuntimeError("Stack trace test")

    # 调用异常处理器
    with caplog.at_level("ERROR"):
        response = asyncio.run(generic_exception_handler(mock_request, test_exception))

    assert response.status_code == 500

    # 验证日志记录包含堆栈信息
    error_logs = [r for r in caplog.records if r.levelname == "ERROR"]
    assert len(error_logs) > 0
    # exc_info=True 会在日志记录中包含异常信息
    assert any(r.exc_info is not None for r in error_logs)


def test_global_exception_handler_safe_attribute_access():
    """测试全局异常处理器安全访问request.state属性"""
    from unittest.mock import Mock, PropertyMock
    error_monitor.clear()

    # 创建一个request mock，state没有request_id和user_id属性
    mock_request = Mock(spec=Request)
    mock_request.url.path = "/api/test"
    mock_request.method = "GET"
    # 创建一个空的state对象，getattr会返回None
    mock_request.state = Mock(spec=[])  # spec=[] 表示没有任何属性

    # 创建测试异常
    test_exception = ValueError("Test without context")

    # 调用异常处理器不应该崩溃
    response = asyncio.run(generic_exception_handler(mock_request, test_exception))

    assert response.status_code == 500

    # 验证错误被记录，使用了默认值
    recent_errors = error_monitor.get_recent_errors()
    assert len(recent_errors) > 0
    assert recent_errors[-1].request_id == "unknown"
    assert recent_errors[-1].user_id is None


def test_global_exception_handler_no_sensitive_data_leak():
    """测试全局异常处理器不泄露敏感信息"""
    from unittest.mock import patch
    error_monitor.clear()

    # 创建模拟请求（API路径）
    mock_request = MagicMock(spec=Request)
    mock_request.url.path = "/api/test"
    mock_request.method = "GET"
    mock_request.state.request_id = "test-req-security"
    mock_request.state.user_id = None

    # 创建包含敏感路径信息的异常
    test_exception = Exception("Error in /secret/internal/path/file.py line 42: database connection failed")

    # 调用异常处理器
    response = asyncio.run(generic_exception_handler(mock_request, test_exception))

    assert response.status_code == 500

    # 验证响应不包含敏感信息
    import json
    response_data = json.loads(response.body.decode())

    # 验证响应不包含文件路径、行号等敏感信息
    response_str = str(response_data)
    assert "/secret/" not in response_str
    assert "file.py" not in response_str
    assert "line 42" not in response_str
    assert "database connection" not in response_str

    # 只返回通用错误消息
    assert response_data["message"] == "系统错误"
    assert response_data["code"] == 10000
    assert response_data["data"] is None


def test_login_success_logs_operation(client, db_session, caplog):
    """测试登录成功记录日志"""
    from app.models import User

    # 创建测试用户
    user = User(
        username="testuser",
        password_hash=User.hash_password("Test123!@#"),
        role="student",
        display_name="Test User"
    )
    db_session.add(user)
    db_session.commit()

    csrf = get_csrf_token(client)
    with caplog.at_level("INFO"):
        response = client.post("/login", data={
            "username": "testuser",
            "password": "Test123!@#",
            "_csrf_token": csrf
        })

    assert response.status_code == 303  # 重定向

    # 验证日志
    login_logs = [r for r in caplog.records if "login_success" in r.message or "Login successful" in r.message]
    assert len(login_logs) > 0


def test_login_failure_logs_warning(client, caplog):
    """测试登录失败记录警告日志"""
    csrf = get_csrf_token(client)
    with caplog.at_level("WARNING"):
        response = client.post("/login", data={
            "username": "nonexistent",
            "password": "wrongpass",
            "_csrf_token": csrf
        })

    # 验证警告日志
    warning_logs = [r for r in caplog.records if r.levelname == "WARNING" and ("login" in r.message.lower() or "failed" in r.message.lower())]
    assert len(warning_logs) > 0

