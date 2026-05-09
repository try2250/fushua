from datetime import datetime, timedelta
from tests.conftest import create_test_user, register_and_login, get_csrf_token
from app.models import User, ClassGroup, ClassMember, SiteConfig


class TestAdminIndex:
    def test_admin_index_requires_login(self, client, db_session):
        response = client.get("/admin", follow_redirects=False)
        assert response.status_code == 303

    def test_admin_index_requires_admin(self, client, db_session):
        register_and_login(client, "normalstudent", "student")
        response = client.get("/admin", follow_redirects=False)
        assert response.status_code == 403

    def test_admin_index_shows_stats(self, client, db_session):
        admin = create_test_user(db_session, "adminuser", "teacher")
        admin.is_admin = True
        db_session.commit()
        register_and_login(client, "adminuser", "teacher")
        response = client.get("/admin", follow_redirects=True)
        assert response.status_code == 200
        assert "用户数" in response.text
        assert "班级数" in response.text
        assert "题目数" in response.text


class TestAdminUsers:
    def test_admin_users_list(self, client, db_session):
        admin = create_test_user(db_session, "adminuser2", "teacher")
        admin.is_admin = True
        db_session.commit()
        create_test_user(db_session, "liststudent", "student")
        register_and_login(client, "adminuser2", "teacher")
        response = client.get("/admin/users", follow_redirects=True)
        assert response.status_code == 200
        assert "liststudent" in response.text

    def test_admin_users_search(self, client, db_session):
        admin = create_test_user(db_session, "adminuser3", "teacher")
        admin.is_admin = True
        db_session.commit()
        create_test_user(db_session, "searchstudent", "student")
        create_test_user(db_session, "otherstudent", "student")
        register_and_login(client, "adminuser3", "teacher")
        response = client.get("/admin/users?q=search", follow_redirects=True)
        assert response.status_code == 200
        assert "searchstudent" in response.text
        assert "otherstudent" not in response.text

    def test_admin_users_filter_by_role(self, client, db_session):
        admin = create_test_user(db_session, "adminuser4", "teacher")
        admin.is_admin = True
        db_session.commit()
        create_test_user(db_session, "filterstudent", "student")
        register_and_login(client, "adminuser4", "teacher")
        response = client.get("/admin/users?role=student", follow_redirects=True)
        assert response.status_code == 200
        assert "filterstudent" in response.text

    def test_admin_users_requires_admin(self, client, db_session):
        register_and_login(client, "normalstudent2", "student")
        response = client.get("/admin/users", follow_redirects=False)
        assert response.status_code == 403


class TestAdminResetPassword:
    def test_reset_password(self, client, db_session):
        admin = create_test_user(db_session, "adminuser5", "teacher")
        admin.is_admin = True
        db_session.commit()
        target = create_test_user(db_session, "resetstudent", "student")
        register_and_login(client, "adminuser5", "teacher")
        csrf = get_csrf_token(client)
        response = client.post(f"/admin/users/{target.id}/reset-password", data={
            "_csrf_token": csrf,
        })
        assert response.status_code == 303
        db_session.expire_all()
        updated = db_session.query(User).filter(User.id == target.id).first()
        assert User.verify_password(updated.password_hash, "abc123")

    def test_reset_password_nonexistent_user(self, client, db_session):
        admin = create_test_user(db_session, "adminuser6", "teacher")
        admin.is_admin = True
        db_session.commit()
        register_and_login(client, "adminuser6", "teacher")
        csrf = get_csrf_token(client)
        response = client.post("/admin/users/9999/reset-password", data={
            "_csrf_token": csrf,
        })
        assert response.status_code == 404


class TestAdminToggleDisable:
    def test_disable_user(self, client, db_session):
        admin = create_test_user(db_session, "adminuser7", "teacher")
        admin.is_admin = True
        db_session.commit()
        target = create_test_user(db_session, "disablestudent", "student")
        register_and_login(client, "adminuser7", "teacher")
        csrf = get_csrf_token(client)
        response = client.post(f"/admin/users/{target.id}/toggle-disable", data={
            "_csrf_token": csrf,
        })
        assert response.status_code == 303
        db_session.expire_all()
        updated = db_session.query(User).filter(User.id == target.id).first()
        assert updated.is_disabled is True

    def test_enable_user(self, client, db_session):
        admin = create_test_user(db_session, "adminuser8", "teacher")
        admin.is_admin = True
        db_session.commit()
        target = create_test_user(db_session, "enablestudent", "student")
        target.is_disabled = True
        db_session.commit()
        register_and_login(client, "adminuser8", "teacher")
        csrf = get_csrf_token(client)
        response = client.post(f"/admin/users/{target.id}/toggle-disable", data={
            "_csrf_token": csrf,
        })
        assert response.status_code == 303
        db_session.expire_all()
        updated = db_session.query(User).filter(User.id == target.id).first()
        assert updated.is_disabled is False

    def test_cannot_disable_admin(self, client, db_session):
        admin = create_test_user(db_session, "adminuser9", "teacher")
        admin.is_admin = True
        db_session.commit()
        other_admin = create_test_user(db_session, "otheradmin", "teacher")
        other_admin.is_admin = True
        db_session.commit()
        register_and_login(client, "adminuser9", "teacher")
        csrf = get_csrf_token(client)
        response = client.post(f"/admin/users/{other_admin.id}/toggle-disable", data={
            "_csrf_token": csrf,
        })
        assert response.status_code == 403


class TestAdminCleanupGuests:
    def test_cleanup_expired_guests(self, client, db_session):
        admin = create_test_user(db_session, "adminuser10", "teacher")
        admin.is_admin = True
        db_session.commit()
        expired_guest = User(
            username="expiredguest",
            password_hash=User.hash_password("abc123"),
            role="student",
            display_name="expiredguest",
            is_guest=True,
            guest_expires_at=datetime.now() - timedelta(hours=1),
        )
        db_session.add(expired_guest)
        db_session.commit()
        register_and_login(client, "adminuser10", "teacher")
        csrf = get_csrf_token(client)
        response = client.post("/admin/cleanup-guests", data={
            "_csrf_token": csrf,
        })
        assert response.status_code == 303
        db_session.expire_all()
        remaining = db_session.query(User).filter(User.username == "expiredguest").first()
        assert remaining is None

    def test_cleanup_keeps_active_guests(self, client, db_session):
        admin = create_test_user(db_session, "adminuser11", "teacher")
        admin.is_admin = True
        db_session.commit()
        active_guest = User(
            username="activeguest",
            password_hash=User.hash_password("abc123"),
            role="student",
            display_name="activeguest",
            is_guest=True,
            guest_expires_at=datetime.now() + timedelta(hours=1),
        )
        db_session.add(active_guest)
        db_session.commit()
        register_and_login(client, "adminuser11", "teacher")
        csrf = get_csrf_token(client)
        response = client.post("/admin/cleanup-guests", data={
            "_csrf_token": csrf,
        })
        assert response.status_code == 303
        db_session.expire_all()
        remaining = db_session.query(User).filter(User.username == "activeguest").first()
        assert remaining is not None


class TestDisabledUserLogin:
    def test_disabled_user_cannot_login(self, client, db_session):
        user = create_test_user(db_session, "disableduser", "student")
        user.is_disabled = True
        db_session.commit()
        csrf = get_csrf_token(client)
        response = client.post("/login", data={
            "username": "disableduser",
            "password": "abc123",
            "_csrf_token": csrf,
        })
        assert response.status_code == 200
        assert "账号已被禁用" in response.text
