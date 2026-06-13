"""平台用户管理测试"""
from fastapi.testclient import TestClient
from app.main import app as main_app
from app.models import User


def _login_platform(client, platform_admin):
    from tests.conftest import get_csrf_token
    csrf = get_csrf_token(client)
    return client.post("/platform/login", data={"username": platform_admin.username, "password": "rootpass", "_csrf_token": csrf}, follow_redirects=False)


def test_platform_users_lists_all(db, platform_admin):
    db.add_all([User(username="t1@x.cn", password_hash=User.hash_password("x"), role="teacher", display_name="T1"), User(username="s1", password_hash=User.hash_password("x"), role="student", display_name="S1")])
    db.commit()
    client = TestClient(main_app, follow_redirects=False)
    _login_platform(client, platform_admin)
    r = client.get("/platform/users")
    assert r.status_code == 200
    body = r.text
    assert "t1@x.cn" in body and "s1" in body


def test_platform_users_search_by_username(db, platform_admin):
    db.add(User(username="found_me", password_hash=User.hash_password("x"), role="student", display_name="X"))
    db.commit()
    client = TestClient(main_app, follow_redirects=False)
    _login_platform(client, platform_admin)
    r = client.get("/platform/users?q=found_me")
    assert r.status_code == 200
    assert "found_me" in r.text


def test_platform_users_unauthenticated_redirects_to_login(db):
    client = TestClient(main_app, follow_redirects=False)
    r = client.get("/platform/users")
    assert r.status_code in (303, 307)


def test_platform_user_reset_password(db, platform_admin):
    u = User(username="resetme", password_hash=User.hash_password("oldpass"), role="student", display_name="x")
    db.add(u); db.commit(); db.refresh(u)
    client = TestClient(main_app, follow_redirects=False)
    _login_platform(client, platform_admin)
    from tests.conftest import get_csrf_token
    csrf = get_csrf_token(client)
    r = client.post(f"/platform/users/{u.id}/reset-password", data={"_csrf_token": csrf}, follow_redirects=False)
    assert r.status_code == 303
    db.refresh(u)
    assert User.verify_password(u.password_hash, "abc12345") is True
    assert u.force_password_change is True
