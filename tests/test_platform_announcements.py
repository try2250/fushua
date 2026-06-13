"""平台公告管理测试"""
from fastapi.testclient import TestClient
from app.main import app as main_app
from app.models import Announcement


def _login(client, pa):
    from tests.conftest import get_csrf_token
    csrf = get_csrf_token(client)
    client.post("/platform/login", data={"username": pa.username, "password": "rootpass", "_csrf_token": csrf}, follow_redirects=False)


def test_announcements_list(db, platform_admin):
    db.add(Announcement(title="维护通知", content="周三停服", is_active=True))
    db.commit()
    client = TestClient(main_app, follow_redirects=False)
    _login(client, platform_admin)
    r = client.get("/platform/announcements")
    assert r.status_code == 200
    assert "维护通知" in r.text


def test_announcement_create(db, platform_admin):
    client = TestClient(main_app, follow_redirects=False)
    _login(client, platform_admin)
    from tests.conftest import get_csrf_token
    csrf = get_csrf_token(client)
    r = client.post("/platform/announcements/create", data={"title": "新公告", "content": "内容", "is_active": "on", "_csrf_token": csrf}, follow_redirects=False)
    assert r.status_code == 303
    a = db.query(Announcement).filter(Announcement.title == "新公告").first()
    assert a is not None and a.is_active is True


def test_announcement_toggle(db, platform_admin):
    a = Announcement(title="x", content="x", is_active=True)
    db.add(a); db.commit(); db.refresh(a)
    client = TestClient(main_app, follow_redirects=False)
    _login(client, platform_admin)
    from tests.conftest import get_csrf_token
    csrf = get_csrf_token(client)
    r = client.post(f"/platform/announcements/{a.id}/toggle", data={"_csrf_token": csrf}, follow_redirects=False)
    assert r.status_code == 303
    db.refresh(a)
    assert a.is_active is False


def test_announcement_delete(db, platform_admin):
    a = Announcement(title="x", content="x", is_active=True)
    db.add(a); db.commit(); db.refresh(a)
    client = TestClient(main_app, follow_redirects=False)
    _login(client, platform_admin)
    from tests.conftest import get_csrf_token
    csrf = get_csrf_token(client)
    r = client.post(f"/platform/announcements/{a.id}/delete", data={"_csrf_token": csrf}, follow_redirects=False)
    assert r.status_code == 303
    assert db.query(Announcement).filter(Announcement.id == a.id).first() is None
