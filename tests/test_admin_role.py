import pytest
from tests.conftest import create_test_user, get_csrf_token, TestingSessionLocal, register_and_login
from app.models import User, SiteConfig


class TestAdminRole:
    def test_register_admin_with_invite_code(self, client, db_session):
        config = SiteConfig(key="admin_invite_code", value="ADMIN2026")
        db_session.add(config)
        db_session.commit()
        csrf = get_csrf_token(client)
        resp = client.post("/register", data={
            "username": "admin_user",
            "password": "admin123",
            "role": "admin",
            "display_name": "管理员",
            "invite_code": "ADMIN2026",
            "_csrf_token": csrf,
        }, follow_redirects=False)
        assert resp.status_code == 303
        user = db_session.query(User).filter(User.username == "admin_user").first()
        assert user is not None
        assert user.role == "admin"

    def test_register_admin_without_invite_code_is_error(self, client, db_session):
        csrf = get_csrf_token(client)
        resp = client.post("/register", data={
            "username": "no_code_admin",
            "password": "admin123",
            "role": "admin",
            "display_name": "无码管理员",
            "_csrf_token": csrf,
        }, follow_redirects=True)
        assert "邀请码" in resp.text

    def test_register_admin_with_wrong_invite_code_is_error(self, client, db_session):
        config = SiteConfig(key="admin_invite_code", value="ADMIN2026")
        db_session.add(config)
        db_session.commit()
        csrf = get_csrf_token(client)
        resp = client.post("/register", data={
            "username": "wrong_code_admin",
            "password": "admin123",
            "role": "admin",
            "display_name": "错码管理员",
            "invite_code": "WRONG",
            "_csrf_token": csrf,
        }, follow_redirects=True)
        assert "邀请码无效" in resp.text

    def test_require_admin_role_allows_admin(self, client, db_session):
        from app.auth import require_admin_role
        admin = create_test_user(db_session, username="role_admin", role="admin")
        db_session.commit()
        request = type("Request", (), {"session": {"user_id": admin.id}})()
        result = require_admin_role(request, db_session)
        assert result == admin.id

    def test_require_admin_role_rejects_teacher(self, client, db_session):
        from app.auth import require_admin_role
        from fastapi import HTTPException
        teacher = create_test_user(db_session, username="not_admin_teacher", role="teacher")
        teacher.is_admin = True
        db_session.commit()
        request = type("Request", (), {"session": {"user_id": teacher.id}})()
        with pytest.raises(HTTPException) as exc_info:
            require_admin_role(request, db_session)
        assert exc_info.value.status_code == 403

    def test_require_admin_role_rejects_student(self, client, db_session):
        from app.auth import require_admin_role
        from fastapi import HTTPException
        student = create_test_user(db_session, username="not_admin_student", role="student")
        db_session.commit()
        request = type("Request", (), {"session": {"user_id": student.id}})()
        with pytest.raises(HTTPException) as exc_info:
            require_admin_role(request, db_session)
        assert exc_info.value.status_code == 403

    def test_admin_can_access_admin_panel(self, client, db_session):
        admin = create_test_user(db_session, username="panel_admin", role="admin")
        db_session.commit()
        register_and_login(client, username="panel_admin", role="admin")
        resp = client.get("/admin", follow_redirects=False)
        assert resp.status_code == 200 or resp.status_code == 303

    def test_teacher_cannot_access_admin_panel(self, client, db_session):
        teacher = create_test_user(db_session, username="no_panel_teacher", role="teacher")
        teacher.is_admin = True
        db_session.commit()
        register_and_login(client, username="no_panel_teacher", role="teacher")
        resp = client.get("/admin", follow_redirects=False)
        assert resp.status_code == 403


class TestAdminPanelAccess:
    def test_admin_panel_shows_admin_features(self, client, db_session):
        admin = create_test_user(db_session, username="feat_admin", role="admin")
        db_session.commit()
        register_and_login(client, username="feat_admin", role="admin")
        resp = client.get("/admin", follow_redirects=True)
        assert resp.status_code == 200
        assert "管理后台" in resp.text

    def test_admin_can_manage_invite_codes(self, client, db_session):
        admin = create_test_user(db_session, username="invite_admin", role="admin")
        db_session.commit()
        register_and_login(client, username="invite_admin", role="admin")
        resp = client.get("/admin/invite", follow_redirects=True)
        assert resp.status_code == 200

    def test_admin_can_set_teacher_admin_flag(self, client, db_session):
        admin = create_test_user(db_session, username="flag_admin", role="admin")
        teacher = create_test_user(db_session, username="flag_teacher", role="teacher")
        db_session.commit()
        register_and_login(client, username="flag_admin", role="admin")
        csrf = get_csrf_token(client)
        resp = client.post(f"/admin/users/{teacher.id}/toggle-admin", data={
            "_csrf_token": csrf,
        }, follow_redirects=False)
        assert resp.status_code == 303
        db_session.refresh(teacher)
        assert teacher.is_admin is True

    def test_admin_users_page_shows_admin_role(self, client, db_session):
        admin = create_test_user(db_session, username="list_admin", role="admin")
        db_session.commit()
        register_and_login(client, username="list_admin", role="admin")
        resp = client.get("/admin/users?role=admin", follow_redirects=True)
        assert resp.status_code == 200
        assert "管理员" in resp.text


class TestAdminNavigation:
    def test_admin_sees_admin_nav(self, client, db_session):
        admin = create_test_user(db_session, username="nav_admin", role="admin")
        db_session.commit()
        register_and_login(client, username="nav_admin", role="admin")
        resp = client.get("/", follow_redirects=True)
        assert "管理后台" in resp.text or "/admin" in resp.text

    def test_teacher_no_admin_nav(self, client, db_session):
        teacher = create_test_user(db_session, username="nav_teacher", role="teacher")
        db_session.commit()
        register_and_login(client, username="nav_teacher", role="teacher")
        resp = client.get("/", follow_redirects=True)
        text = resp.text
        has_admin_nav = "管理后台" in text and 'href="/admin"' in text
        assert not has_admin_nav
