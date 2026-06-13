"""Plan 1.2B — 邮箱验证码 + 教师邮箱注册测试"""
import pytest
from fastapi.testclient import TestClient
from app.main import app as main_app
from app.models import User
from app.services.email_service import email_service, EmailServiceError


def test_generate_and_verify_code(db):
    code = email_service.generate_code(db, "a@b.com", purpose="register")
    assert code.isdigit() and len(code) == 6
    assert email_service.verify_code(db, "a@b.com", code, purpose="register") is True
    assert email_service.verify_code(db, "a@b.com", code, purpose="register") is False


def test_wrong_code_rejected(db):
    email_service.generate_code(db, "a@b.com", purpose="register")
    assert email_service.verify_code(db, "a@b.com", "999999", purpose="register") is False


def test_rate_limit_5_per_hour(db):
    for _ in range(5):
        email_service.generate_code(db, "a@b.com", purpose="register")
    with pytest.raises(EmailServiceError):
        email_service.generate_code(db, "a@b.com", purpose="register")


# ─── Task 4: API register-teacher ───


def test_register_teacher_with_valid_code_succeeds(db):
    code = email_service.generate_code(db, "li@school.cn", "register")
    client = TestClient(main_app)
    r = client.post("/api/v1/auth/register-teacher", json={
        "email": "li@school.cn",
        "password": "abc12345",
        "display_name": "李老师",
        "code": code,
    })
    assert r.status_code == 200
    body = r.json()["data"]
    assert "token" in body
    u = db.query(User).filter(User.username == "li@school.cn").first()
    assert u is not None
    assert u.role == "teacher"


def test_register_teacher_wrong_code_returns_400(db):
    email_service.generate_code(db, "x@y.cn", "register")
    client = TestClient(main_app)
    r = client.post("/api/v1/auth/register-teacher", json={
        "email": "x@y.cn",
        "password": "abc12345",
        "display_name": "x",
        "code": "000000",
    })
    assert r.status_code == 400


def test_register_teacher_duplicate_email_returns_400(db):
    db.add(User(username="dup@y.cn", password_hash=User.hash_password("x"),
                role="teacher", display_name="x"))
    db.commit()
    code = email_service.generate_code(db, "dup@y.cn", "register")
    client = TestClient(main_app)
    r = client.post("/api/v1/auth/register-teacher", json={
        "email": "dup@y.cn",
        "password": "abc12345",
        "display_name": "x",
        "code": code,
    })
    assert r.status_code == 400