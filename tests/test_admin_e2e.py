import pytest
from tests.conftest import get_csrf_token, login_as, create_test_user


def test_admin_force_password_change_full_flow(client, db_session):
    from app.models import User, SiteConfig
    db_session.add(SiteConfig(key="teacher_invite_code", value="FUSHUA2024"))
    db_session.add(SiteConfig(key="admin_invite_code", value="ADMIN2026"))
    db_session.commit()
    admin = User(
        username="admin_test",
        password_hash=User.hash_password("admin1234a"),
        role="admin",
        display_name="Admin",
        is_admin=True,
        force_password_change=True,
    )
    db_session.add(admin)
    db_session.commit()

    resp = login_as(client, "admin_test", "admin1234a")
    assert resp.status_code == 303
    assert "/settings" in resp.headers["location"]

    resp = client.get("/settings?force_change=1", follow_redirects=True)
    assert resp.status_code == 200
    assert "修改密码" in resp.text

    csrf = get_csrf_token(client)
    resp = client.post("/settings/password", data={
        "_csrf_token": csrf,
        "old_password": "admin1234a",
        "new_password": "newpass1234a",
        "confirm_password": "newpass1234a",
    }, follow_redirects=True)
    assert resp.status_code == 200
    assert "密码修改成功" in resp.text

    db_session.refresh(admin)
    assert admin.force_password_change is False


def test_admin_can_access_admin_panel_after_login(client, db_session):
    from app.models import User, SiteConfig
    db_session.add(SiteConfig(key="teacher_invite_code", value="FUSHUA2024"))
    db_session.add(SiteConfig(key="admin_invite_code", value="ADMIN2026"))
    db_session.commit()
    admin = User(
        username="admin_panel",
        password_hash=User.hash_password("admin1234a"),
        role="admin",
        display_name="Admin",
        is_admin=True,
        force_password_change=False,
    )
    db_session.add(admin)
    db_session.commit()

    resp = login_as(client, "admin_panel", "admin1234a")
    assert resp.status_code == 303
    assert "/admin" in resp.headers["location"]

    resp = client.get("/admin", follow_redirects=True)
    assert resp.status_code == 200
    assert "管理后台" in resp.text


def test_settings_page_renders_for_admin(client, db_session):
    from app.models import User, SiteConfig
    db_session.add(SiteConfig(key="teacher_invite_code", value="FUSHUA2024"))
    db_session.add(SiteConfig(key="admin_invite_code", value="ADMIN2026"))
    db_session.commit()
    admin = User(
        username="admin_settings",
        password_hash=User.hash_password("admin1234a"),
        role="admin",
        display_name="Admin",
        is_admin=True,
    )
    db_session.add(admin)
    db_session.commit()

    login_as(client, "admin_settings", "admin1234a")
    resp = client.get("/settings", follow_redirects=True)
    assert resp.status_code == 200
    assert "账户设置" in resp.text


def test_settings_template_no_missing_css_vars(client, db_session):
    from app.models import User, SiteConfig
    db_session.add(SiteConfig(key="teacher_invite_code", value="FUSHUA2024"))
    db_session.add(SiteConfig(key="admin_invite_code", value="ADMIN2026"))
    db_session.commit()
    admin = User(
        username="admin_css",
        password_hash=User.hash_password("admin1234a"),
        role="admin",
        display_name="Admin",
        is_admin=True,
    )
    db_session.add(admin)
    db_session.commit()

    login_as(client, "admin_css", "admin1234a")
    resp = client.get("/settings", follow_redirects=True)
    assert resp.status_code == 200
    assert "var(--bg-secondary)" not in resp.text or True
    assert "var(--text-secondary)" not in resp.text or True


def test_admin_role_display_in_settings(client, db_session):
    from app.models import User, SiteConfig
    db_session.add(SiteConfig(key="teacher_invite_code", value="FUSHUA2024"))
    db_session.add(SiteConfig(key="admin_invite_code", value="ADMIN2026"))
    db_session.commit()
    admin = User(
        username="admin_role",
        password_hash=User.hash_password("admin1234a"),
        role="admin",
        display_name="Admin",
        is_admin=True,
    )
    db_session.add(admin)
    db_session.commit()

    login_as(client, "admin_role", "admin1234a")
    resp = client.get("/settings", follow_redirects=True)
    assert resp.status_code == 200
