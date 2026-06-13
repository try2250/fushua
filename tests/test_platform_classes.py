"""平台班级总览测试"""
from fastapi.testclient import TestClient
from app.main import app as main_app
from app.models import ClassGroup


def _login(client, pa):
    from tests.conftest import get_csrf_token
    csrf = get_csrf_token(client)
    client.post("/platform/login", data={
        "username": pa.username, "password": "rootpass", "_csrf_token": csrf,
    }, follow_redirects=False)


def test_platform_classes_lists_all_across_tenants(db, platform_admin, teacher_a, teacher_b):
    db.add_all([
        ClassGroup(name="A 的班", created_by=teacher_a.id),
        ClassGroup(name="B 的班", created_by=teacher_b.id),
    ])
    db.commit()
    client = TestClient(main_app, follow_redirects=False)
    _login(client, platform_admin)
    r = client.get("/platform/classes")
    assert r.status_code == 200
    assert "A 的班" in r.text and "B 的班" in r.text
