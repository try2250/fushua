"""
测试微信绑定手机号功能，特别是 PHONE_BINDING_REQUIRE_SMS 开关
"""
import pytest
from app.models import User, VerificationCode
from app.core.security import create_access_token
from app.core.config import settings
from datetime import datetime, timedelta, timezone


@pytest.fixture
def sms_required():
    original_config = settings.PHONE_BINDING_REQUIRE_SMS
    yield
    settings.PHONE_BINDING_REQUIRE_SMS = original_config


def test_bind_without_sms_when_disabled(client, db_session, sms_required):
    """测试：PHONE_BINDING_REQUIRE_SMS=false 时，不需要验证码可以绑定"""
    settings.PHONE_BINDING_REQUIRE_SMS = False

    openid = "test_openid_123"
    temp_token = create_access_token(
        {"openid": openid, "temp": True},
        expires_delta=timedelta(minutes=10)
    )

    response = client.post("/api/v1/auth/wechat/bind", json={
        "openid_token": temp_token,
        "phone": "13800138000",
        "code": "",
        "role": "student",
        "class_id": None
    })

    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 0
    assert "token" in data["data"]

    user = db_session.query(User).filter(User.phone == "13800138000").first()
    assert user is not None
    assert user.is_phone_verified == False
    assert user.openid == openid


def test_bind_with_wrong_phone_format(client, sms_required):
    """测试：即使免验证码，错误的手机号格式也不能绑定"""
    settings.PHONE_BINDING_REQUIRE_SMS = False

    openid = "test_openid_456"
    temp_token = create_access_token(
        {"openid": openid, "temp": True},
        expires_delta=timedelta(minutes=10)
    )

    response = client.post("/api/v1/auth/wechat/bind", json={
        "openid_token": temp_token,
        "phone": "12345",
        "code": "",
        "role": "student",
        "class_id": None
    })

    assert response.status_code == 422


def test_bind_duplicate_phone(client, db_session, sms_required):
    """测试：免验证码时，重复手机号仍不能绑定"""
    settings.PHONE_BINDING_REQUIRE_SMS = False

    existing_user = User(
        username="existing_user",
        password_hash="",
        role="student",
        phone="13800138001",
        openid="existing_openid"
    )
    db_session.add(existing_user)
    db_session.commit()

    openid = "test_openid_789"
    temp_token = create_access_token(
        {"openid": openid, "temp": True},
        expires_delta=timedelta(minutes=10)
    )

    response = client.post("/api/v1/auth/wechat/bind", json={
        "openid_token": temp_token,
        "phone": "13800138001",
        "code": "",
        "role": "student",
        "class_id": None
    })

    assert response.status_code == 400
    response_data = response.json()
    error_msg = response_data.get("message") or response_data.get("detail", "")
    assert "已注册" in error_msg or "注册" in error_msg


def test_bind_with_sms_enabled(client, db_session, sms_required):
    """测试：PHONE_BINDING_REQUIRE_SMS=true 时，需要正确验证码"""
    settings.PHONE_BINDING_REQUIRE_SMS = True

    verification = VerificationCode(
        phone="13800138002",
        code="123456",
        purpose="bind",
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=5)
    )
    db_session.add(verification)
    db_session.commit()

    openid = "test_openid_with_sms"
    temp_token = create_access_token(
        {"openid": openid, "temp": True},
        expires_delta=timedelta(minutes=10)
    )

    response = client.post("/api/v1/auth/wechat/bind", json={
        "openid_token": temp_token,
        "phone": "13800138002",
        "code": "123456",
        "role": "student",
        "class_id": None
    })

    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 0

    user = db_session.query(User).filter(User.phone == "13800138002").first()
    assert user is not None
    assert user.is_phone_verified == True


def test_bind_with_sms_enabled_wrong_code(client, sms_required):
    """测试：PHONE_BINDING_REQUIRE_SMS=true 时，错误验证码不能绑定"""
    settings.PHONE_BINDING_REQUIRE_SMS = True

    openid = "test_openid_wrong_code"
    temp_token = create_access_token(
        {"openid": openid, "temp": True},
        expires_delta=timedelta(minutes=10)
    )

    response = client.post("/api/v1/auth/wechat/bind", json={
        "openid_token": temp_token,
        "phone": "13800138003",
        "code": "999999",
        "role": "student",
        "class_id": None
    })

    assert response.status_code == 400
    response_data = response.json()
    error_msg = response_data.get("message") or response_data.get("detail", "")
    assert "验证码" in error_msg
