"""E2E：PlatformAdmin 登录 → 看用户 → 创建公告 → 导出数据。"""
from app.models import User, Announcement


def test_platform_admin_full_journey(client, db, platform_admin_logged_in):
    c = platform_admin_logged_in

    r = c.get("/platform/dashboard")
    assert r.status_code == 200

    db.add_all([
        User(username="pa_t@x.cn", password_hash=User.hash_password("x"), role="teacher", display_name="PA-T"),
        User(username="pa_s", password_hash=User.hash_password("x"), role="student", display_name="PA-S"),
    ])
    db.commit()
    r = c.get("/platform/users")
    assert r.status_code == 200
    assert "pa_t@x.cn" in r.text and "pa_s" in r.text

    from tests.e2e.conftest import _csrf
    csrf = _csrf(c)
    r = c.post("/platform/announcements/create", data={"title": "E2E 平台公告", "content": "测试内容", "is_active": "on", "_csrf_token": csrf}, follow_redirects=False)
    assert r.status_code == 303

    r = c.get("/platform/announcements")
    assert r.status_code == 200
    assert "E2E 平台公告" in r.text

    r = c.get("/platform/export/users")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/csv")
    assert "pa_t@x.cn" in r.text
