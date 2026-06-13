"""平台数据导出测试"""
from fastapi.testclient import TestClient
from app.main import app as main_app
from app.models import User


def _login(client, pa):
    from tests.conftest import get_csrf_token
    csrf = get_csrf_token(client)
    client.post("/platform/login", data={"username": pa.username, "password": "rootpass", "_csrf_token": csrf}, follow_redirects=False)


def test_export_users_csv(db, platform_admin):
    db.add(User(username="u1@x.cn", password_hash=User.hash_password("x"), role="teacher", display_name="U1"))
    db.commit()
    client = TestClient(main_app, follow_redirects=False)
    _login(client, platform_admin)
    r = client.get("/platform/export/users")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/csv")
    assert "u1@x.cn" in r.text
