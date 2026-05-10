import pytest
from tests.conftest import create_test_user, get_csrf_token, register_and_login
from app.models import User, SiteConfig


class TestSessionValidation:
    def test_disabled_user_cannot_access(self, client, db_session):
        user = create_test_user(db_session, username="disabled_user", role="student")
        user.is_disabled = True
        db_session.commit()
        register_and_login(client, username="disabled_user", role="student")
        resp = client.get("/student/dashboard", follow_redirects=False)
        assert resp.status_code in (303, 403)


class TestSanitizeXSS:
    def test_sanitize_strips_html(self):
        from app.security import sanitize_input
        result = sanitize_input("<script>alert(1)</script>hello")
        assert "<script>" not in result

    def test_sanitize_strips_js_events(self):
        from app.security import sanitize_input
        result = sanitize_input('text"onclick="alert(1)')
        assert "onclick" not in result


class TestAdminRedirect:
    def test_admin_login_redirects_to_admin(self, client, db_session):
        admin = create_test_user(db_session, username="redir_admin", role="admin")
        db_session.commit()
        csrf = get_csrf_token(client)
        resp = client.post("/login", data={
            "username": "redir_admin",
            "password": "abc12345",
            "_csrf_token": csrf,
        }, follow_redirects=False)
        assert resp.status_code == 303
        assert "/admin" in resp.headers.get("location", "")


class TestDefaultPasswordForceChange:
    def test_reset_password_sets_force_change(self, client, db_session):
        admin = create_test_user(db_session, username="force_admin", role="admin")
        student = create_test_user(db_session, username="force_student")
        db_session.commit()
        register_and_login(client, username="force_admin", role="admin")
        csrf = get_csrf_token(client)
        resp = client.post(f"/admin/users/{student.id}/reset-password", data={
            "_csrf_token": csrf,
        }, follow_redirects=False)
        assert resp.status_code == 303
        db_session.refresh(student)
        assert student.force_password_change is True
