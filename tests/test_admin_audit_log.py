from datetime import datetime, timedelta
from app.models import AuditLog, User
from tests.conftest import create_test_user, register_and_login, get_csrf_token


class TestAdminAuditLogResetPassword:
    def test_reset_password_creates_audit_log(self, client, db_session):
        admin = create_test_user(db_session, "audit_admin_reset", "admin")
        db_session.commit()
        target = create_test_user(db_session, "audit_reset_target", "student")
        register_and_login(client, "audit_admin_reset", "admin")
        csrf = get_csrf_token(client)
        response = client.post(f"/admin/users/{target.id}/reset-password", data={
            "_csrf_token": csrf,
        })
        assert response.status_code == 303
        log = db_session.query(AuditLog).filter(
            AuditLog.action == "reset_password",
            AuditLog.target_id == target.id
        ).first()
        assert log is not None
        assert log.actor_id == admin.id
        assert log.target_type == "user"
        assert log.target_id == target.id
        assert f"管理员重置用户 {target.username} 的密码" in log.detail


class TestAdminAuditLogToggleDisable:
    def test_disable_user_creates_audit_log(self, client, db_session):
        admin = create_test_user(db_session, "audit_admin_disable", "admin")
        db_session.commit()
        target = create_test_user(db_session, "audit_disable_target", "student")
        register_and_login(client, "audit_admin_disable", "admin")
        csrf = get_csrf_token(client)
        response = client.post(f"/admin/users/{target.id}/toggle-disable", data={
            "_csrf_token": csrf,
        })
        assert response.status_code == 303
        log = db_session.query(AuditLog).filter(
            AuditLog.action == "toggle_disable",
            AuditLog.target_id == target.id
        ).first()
        assert log is not None
        assert log.actor_id == admin.id
        assert log.target_type == "user"
        assert log.target_id == target.id
        assert f"禁用用户 {target.username}" in log.detail

    def test_enable_user_creates_audit_log(self, client, db_session):
        admin = create_test_user(db_session, "audit_admin_enable", "admin")
        db_session.commit()
        target = create_test_user(db_session, "audit_enable_target", "student")
        target.is_disabled = True
        db_session.commit()
        register_and_login(client, "audit_admin_enable", "admin")
        csrf = get_csrf_token(client)
        response = client.post(f"/admin/users/{target.id}/toggle-disable", data={
            "_csrf_token": csrf,
        })
        assert response.status_code == 303
        log = db_session.query(AuditLog).filter(
            AuditLog.action == "toggle_disable",
            AuditLog.target_id == target.id
        ).first()
        assert log is not None
        assert log.actor_id == admin.id
        assert log.target_type == "user"
        assert log.target_id == target.id
        assert f"启用用户 {target.username}" in log.detail


class TestAdminAuditLogCleanupGuests:
    def test_cleanup_guests_creates_audit_log(self, client, db_session):
        admin = create_test_user(db_session, "audit_admin_cleanup", "admin")
        db_session.commit()
        expired_guest = User(
            username="audit_expired_guest",
            password_hash=User.hash_password("abc12345"),
            role="student",
            display_name="audit_expired_guest",
            is_guest=True,
            guest_expires_at=datetime.now() - timedelta(hours=1),
        )
        db_session.add(expired_guest)
        db_session.commit()
        register_and_login(client, "audit_admin_cleanup", "admin")
        csrf = get_csrf_token(client)
        response = client.post("/admin/cleanup-guests", data={
            "_csrf_token": csrf,
        })
        assert response.status_code == 303
        log = db_session.query(AuditLog).filter(
            AuditLog.action == "cleanup_guests"
        ).first()
        assert log is not None
        assert log.actor_id == admin.id
        assert log.target_type == "system"
        assert "清理了 1 个过期游客" in log.detail

    def test_cleanup_guests_zero_count(self, client, db_session):
        admin = create_test_user(db_session, "audit_admin_no_guests", "admin")
        db_session.commit()
        register_and_login(client, "audit_admin_no_guests", "admin")
        csrf = get_csrf_token(client)
        response = client.post("/admin/cleanup-guests", data={
            "_csrf_token": csrf,
        })
        assert response.status_code == 303
        log = db_session.query(AuditLog).filter(
            AuditLog.action == "cleanup_guests"
        ).first()
        assert log is not None
        assert log.actor_id == admin.id
        assert "清理了 0 个过期游客" in log.detail


class TestAdminAuditLogActorId:
    def test_audit_log_contains_correct_actor_id(self, client, db_session):
        admin1 = create_test_user(db_session, "audit_actor_admin1", "admin")
        admin2 = create_test_user(db_session, "audit_actor_admin2", "admin")
        db_session.commit()
        target = create_test_user(db_session, "audit_actor_target", "student")
        register_and_login(client, "audit_actor_admin2", "admin")
        csrf = get_csrf_token(client)
        response = client.post(f"/admin/users/{target.id}/reset-password", data={
            "_csrf_token": csrf,
        })
        assert response.status_code == 303
        log = db_session.query(AuditLog).filter(
            AuditLog.action == "reset_password"
        ).first()
        assert log.actor_id == admin2.id
        assert log.actor_id != admin1.id
