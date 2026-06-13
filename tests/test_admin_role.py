import pytest
from tests.conftest import create_test_user, get_csrf_token, TestingSessionLocal, register_and_login
from app.models import User, SiteConfig


def _platform_login(client, platform_admin):
    from tests.conftest import get_csrf_token
    csrf = get_csrf_token(client)
    return client.post("/platform/login", data={
        "username": platform_admin.username, "password": "rootpass", "_csrf_token": csrf,
    }, follow_redirects=False)


class TestAdminRole:
    def test_register_admin_with_invite_code(self, client, db_session, platform_admin):
        pytest.skip("invite codes removed in Plan 1.2B")

    def test_register_admin_without_invite_code_is_error(self, client, db_session, platform_admin):
        csrf = get_csrf_token(client)
        resp = client.post("/register", data={
            "username": "no_code_admin",
            "password": "admin123",
            "role": "admin",
            "display_name": "无码管理员",
            "_csrf_token": csrf,
        }, follow_redirects=True)
        assert "邀请码" in resp.text

    def test_register_admin_with_wrong_invite_code_is_error(self, client, db_session, platform_admin):
        pytest.skip("invite codes removed in Plan 1.2B")

    def test_require_admin_role_allows_admin(self, client, db_session, platform_admin):
        pytest.skip("require_admin_role removed in Plan 1.2B")

    def test_require_admin_role_rejects_teacher(self, client, db_session, platform_admin):
        pytest.skip("require_admin_role removed in Plan 1.2B")

    def test_require_admin_role_rejects_student(self, client, db_session, platform_admin):
        pytest.skip("require_admin_role removed in Plan 1.2B")

    def test_admin_can_access_admin_panel(self, client, db_session, platform_admin):
        _platform_login(client, platform_admin)
        resp = client.get("/platform/dashboard", follow_redirects=False)
        assert resp.status_code == 200

    def test_teacher_cannot_access_admin_panel(self, client, db_session, platform_admin):
        teacher = create_test_user(db_session, username="no_panel_teacher", role="teacher")
        db_session.commit()
        register_and_login(client, username="no_panel_teacher", role="teacher")
        resp = client.get("/platform/dashboard", follow_redirects=False)
        assert resp.status_code == 303


class TestAdminPanelAccess:
    def test_admin_panel_shows_admin_features(self, client, db_session, platform_admin):
        _platform_login(client, platform_admin)
        resp = client.get("/platform/dashboard", follow_redirects=True)
        assert resp.status_code == 200
        assert "教师数" in resp.text

    def test_admin_can_manage_invite_codes(self, client, db_session, platform_admin):
        pytest.skip("invite codes removed in Plan 1.2B")

    def test_admin_can_set_teacher_admin_flag(self, client, db_session, platform_admin):
        pytest.skip("is_admin removed in Plan 1.2B")

    def test_admin_users_page_shows_admin_role(self, client, db_session, platform_admin):
        _platform_login(client, platform_admin)
        resp = client.get("/platform/users?role=teacher", follow_redirects=True)
        assert resp.status_code == 200
        assert "教师" in resp.text


class TestAdminNavigation:
    def test_admin_sees_admin_nav(self, client, db_session, platform_admin):
        _platform_login(client, platform_admin)
        resp = client.get("/platform/dashboard", follow_redirects=True)
        assert resp.status_code == 200
        assert "平台管理" in resp.text

    def test_teacher_no_admin_nav(self, client, db_session, platform_admin):
        teacher = create_test_user(db_session, username="nav_teacher", role="teacher")
        db_session.commit()
        register_and_login(client, username="nav_teacher", role="teacher")
        resp = client.get("/", follow_redirects=True)
        text = resp.text
        has_admin_nav = "管理后台" in text and 'href="/platform"' in text
        assert not has_admin_nav
