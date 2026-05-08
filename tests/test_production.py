import os
import pytest
from tests.conftest import create_test_user, create_test_question, get_csrf_token, login_as, register_and_login
from app.models import Favorite


def test_health_check(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "version" in data


def test_security_headers(client):
    resp = client.get("/")
    assert resp.headers.get("X-Content-Type-Options") == "nosniff"
    assert resp.headers.get("X-Frame-Options") == "DENY"
    assert resp.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
    assert "Content-Security-Policy" in resp.headers
    assert "Permissions-Policy" in resp.headers


def test_csp_header_content(client):
    resp = client.get("/")
    csp = resp.headers.get("Content-Security-Policy", "")
    assert "default-src 'self'" in csp
    assert "frame-ancestors 'none'" in csp


def test_404_error_page(client):
    resp = client.get("/nonexistent-page-12345")
    assert resp.status_code == 404


def test_csrf_required_for_login(client, db_session):
    create_test_user(db_session, username="csrfuser")
    resp = client.post("/login", data={
        "username": "csrfuser",
        "password": "abc123",
    }, follow_redirects=False)
    assert resp.status_code in (403, 400)


def test_csrf_required_for_register(client, db_session):
    resp = client.post("/register", data={
        "username": "newcsrfuser",
        "password": "abc123",
        "role": "student",
        "display_name": "test",
    }, follow_redirects=False)
    assert resp.status_code in (403, 400)


def test_weak_password_rejected(client, db_session):
    csrf = get_csrf_token(client)
    resp = client.post("/register", data={
        "username": "weakpwuser",
        "password": "123",
        "role": "student",
        "display_name": "weakpwuser",
        "_csrf_token": csrf,
    }, follow_redirects=True)
    assert "密码" in resp.text


def test_pure_numeric_password_rejected(client, db_session):
    csrf = get_csrf_token(client)
    resp = client.post("/register", data={
        "username": "numpwuser",
        "password": "123456",
        "role": "student",
        "display_name": "numpwuser",
        "_csrf_token": csrf,
    }, follow_redirects=True)
    assert "密码" in resp.text


def test_short_username_rejected(client, db_session):
    csrf = get_csrf_token(client)
    resp = client.post("/register", data={
        "username": "a",
        "password": "abc123",
        "role": "student",
        "display_name": "test",
        "_csrf_token": csrf,
    }, follow_redirects=True)
    assert "用户名" in resp.text


def test_login_rate_limit(client, db_session):
    create_test_user(db_session, username="ratelimituser")
    for i in range(6):
        csrf = get_csrf_token(client)
        client.post("/login", data={
            "username": "ratelimituser",
            "password": "wrongpass",
            "_csrf_token": csrf,
        }, follow_redirects=False)
    csrf = get_csrf_token(client)
    resp = client.post("/login", data={
        "username": "ratelimituser",
        "password": "abc123",
        "_csrf_token": csrf,
    }, follow_redirects=False)
    assert resp.status_code == 429


def test_logout_requires_post(client, db_session):
    register_and_login(client, username="logouttestuser")
    resp = client.get("/logout", follow_redirects=False)
    assert resp.status_code in (405, 303)


def test_logout_via_post(client, db_session):
    register_and_login(client, username="logoutpostuser")
    csrf = get_csrf_token(client)
    resp = client.post("/logout", data={"_csrf_token": csrf}, follow_redirects=False)
    assert resp.status_code == 303


def test_pwa_icons_accessible(client):
    for path in ["/static/icon-192.png", "/static/icon-512.png"]:
        resp = client.get(path)
        assert resp.status_code == 200


def test_favicon_accessible(client):
    resp = client.get("/static/favicon.ico")
    assert resp.status_code == 200


def test_username_length_limit(client, db_session):
    csrf = get_csrf_token(client)
    long_name = "a" * 200
    resp = client.post("/register", data={
        "username": long_name,
        "password": "abc123",
        "role": "student",
        "display_name": "test",
        "_csrf_token": csrf,
    }, follow_redirects=True)
    assert resp.status_code != 500


def test_teacher_post_requires_csrf(client, db_session):
    create_test_user(db_session, username="teacher_nocsrf", role="teacher")
    login_as(client, "teacher_nocsrf")
    resp = client.post("/teacher/questions/create", data={
        "subject": "数学",
        "content": "test",
        "answer": "A",
    }, follow_redirects=False)
    assert resp.status_code in (403, 400)


def test_student_post_requires_csrf(client, db_session):
    user = create_test_user(db_session, username="student_nocsrf")
    login_as(client, "student_nocsrf")
    q = create_test_question(db_session, created_by=user.id)
    resp = client.post(f"/student/favorites/{q.id}/add", follow_redirects=False)
    assert resp.status_code in (403, 400)
