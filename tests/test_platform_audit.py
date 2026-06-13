"""平台审计日志测试"""
from fastapi.testclient import TestClient
from app.main import app as main_app
from app.models import AuditLog


def _login(client, pa):
    from tests.conftest import get_csrf_token
    csrf = get_csrf_token(client)
    client.post("/platform/login", data={"username": pa.username, "password": "rootpass", "_csrf_token": csrf}, follow_redirects=False)


def test_audit_log_lists_recent_entries(db, platform_admin):
    db.add_all([AuditLog(action="user_login", target_type="user", target_id=1, detail="A"), AuditLog(action="class_create", target_type="class", target_id=1, detail="B")])
    db.commit()
    client = TestClient(main_app, follow_redirects=False)
    _login(client, platform_admin)
    r = client.get("/platform/audit-log")
    assert r.status_code == 200
    assert "user_login" in r.text and "class_create" in r.text


def test_audit_log_filter_by_action(db, platform_admin):
    db.add_all([AuditLog(action="user_login", target_type="user", target_id=1, detail="A"), AuditLog(action="class_create", target_type="class", target_id=1, detail="B")])
    db.commit()
    client = TestClient(main_app, follow_redirects=False)
    _login(client, platform_admin)
    r = client.get("/platform/audit-log?action=user_login")
    assert "user_login" in r.text and "class_create" not in r.text


def test_audit_log_export_csv(db, platform_admin):
    db.add(AuditLog(action="x", target_type="t", target_id=1, detail="d"))
    db.commit()
    client = TestClient(main_app, follow_redirects=False)
    _login(client, platform_admin)
    r = client.get("/platform/audit-log/export")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/csv")
    assert "action,target_type" in r.text
