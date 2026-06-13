"""平台批量清理测试"""
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from app.main import app as main_app
from app.models import User, ClassGroup


def _login(client, pa):
    from tests.conftest import get_csrf_token
    csrf = get_csrf_token(client)
    client.post("/platform/login", data={"username": pa.username, "password": "rootpass", "_csrf_token": csrf}, follow_redirects=False)


def test_batch_cleanup_page_renders(db, platform_admin):
    client = TestClient(main_app, follow_redirects=False)
    _login(client, platform_admin)
    r = client.get("/platform/batch-cleanup")
    assert r.status_code == 200
    assert "批量清理" in r.text


def test_batch_cleanup_expired_guests(db, platform_admin):
    expired = User(username="expired_guest_1", password_hash=User.hash_password("x"), role="student", display_name="过期游客", is_guest=True, guest_expires_at=datetime.utcnow() - timedelta(days=2))
    db.add(expired); db.commit(); db.refresh(expired)
    client = TestClient(main_app, follow_redirects=False)
    _login(client, platform_admin)
    from tests.conftest import get_csrf_token
    csrf = get_csrf_token(client)
    r = client.post("/platform/batch-cleanup", data={"target": "expired_guests", "_csrf_token": csrf}, follow_redirects=False)
    assert r.status_code == 303
    assert db.query(User).filter(User.id == expired.id).first() is None
