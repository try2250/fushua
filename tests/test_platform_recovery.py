"""平台找回申请测试"""
from fastapi.testclient import TestClient
from app.main import app as main_app
from app.models import AccountRecoveryRequest, User, ClassGroup


def _login(client, pa):
    from tests.conftest import get_csrf_token
    csrf = get_csrf_token(client)
    client.post("/platform/login", data={"username": pa.username, "password": "rootpass", "_csrf_token": csrf}, follow_redirects=False)


def test_recovery_requests_lists_pending(db, platform_admin, teacher_a):
    cls = ClassGroup(name="A 班", created_by=teacher_a.id)
    db.add(cls); db.commit(); db.refresh(cls)
    db.add(AccountRecoveryRequest(username="forgot_me", class_id=cls.id, display_name="忘记的人", status="pending"))
    db.commit()
    client = TestClient(main_app, follow_redirects=False)
    _login(client, platform_admin)
    r = client.get("/platform/recovery-requests")
    assert r.status_code == 200
    assert "forgot_me" in r.text


def test_recovery_approve_resets_password(db, platform_admin, teacher_a):
    cls = ClassGroup(name="A", created_by=teacher_a.id)
    db.add(cls); db.commit(); db.refresh(cls)
    target = User(username="needme", password_hash=User.hash_password("old"), role="student", display_name="X")
    db.add(target); db.commit(); db.refresh(target)
    req = AccountRecoveryRequest(username="needme", class_id=cls.id, display_name="X", status="pending")
    db.add(req); db.commit(); db.refresh(req)
    client = TestClient(main_app, follow_redirects=False)
    _login(client, platform_admin)
    from tests.conftest import get_csrf_token
    csrf = get_csrf_token(client)
    r = client.post(f"/platform/recovery-requests/{req.id}/approve", data={"_csrf_token": csrf}, follow_redirects=False)
    assert r.status_code == 303
    db.refresh(target)
    assert User.verify_password(target.password_hash, "abc12345") is True
    db.refresh(req)
    assert req.status == "approved"
