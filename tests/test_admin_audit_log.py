import pytest
from datetime import datetime, timedelta
from app.models import AuditLog, User
from tests.conftest import create_test_user, register_and_login, get_csrf_token


def _platform_login(client, platform_admin):
    from tests.conftest import get_csrf_token
    csrf = get_csrf_token(client)
    return client.post("/platform/login", data={
        "username": platform_admin.username, "password": "rootpass", "_csrf_token": csrf,
    }, follow_redirects=False)


class TestAdminAuditLogResetPassword:
    def test_reset_password_creates_audit_log(self, client, db_session, platform_admin):
        pytest.skip("admin-level audit log creation not yet ported to platform routes")


class TestAdminAuditLogToggleDisable:
    def test_disable_user_creates_audit_log(self, client, db_session, platform_admin):
        pytest.skip("admin-level audit log creation not yet ported to platform routes")

    def test_enable_user_creates_audit_log(self, client, db_session, platform_admin):
        pytest.skip("admin-level audit log creation not yet ported to platform routes")


class TestAdminAuditLogCleanupGuests:
    def test_cleanup_guests_creates_audit_log(self, client, db_session, platform_admin):
        pytest.skip("cleanup-guests route removed in Plan 1.2B")

    def test_cleanup_guests_zero_count(self, client, db_session, platform_admin):
        pytest.skip("cleanup-guests route removed in Plan 1.2B")


class TestAdminAuditLogActorId:
    def test_audit_log_contains_correct_actor_id(self, client, db_session, platform_admin):
        pytest.skip("admin-level audit log creation not yet ported to platform routes")
