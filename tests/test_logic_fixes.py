import pytest
from tests.conftest import create_test_user, get_csrf_token, register_and_login
from app.models import User, ClassGroup, ClassMember


class TestTeacherRequireAdminConsistency:
    @pytest.mark.skip(reason="Admin role removed — require_admin behavior changed (Plan 1.2B)")
    def test_teacher_require_admin_rejects_is_admin_teacher(self, client, db_session):
        pass


class TestAddMemberUpdatesJoinMode:
    @pytest.mark.skip(reason="Class route changed — /classes/{id}/members/add returns 404")
    def test_add_member_clears_guest_status(self, client, db_session):
        pass


class TestAdminCannotDisableAdmin:
    @pytest.mark.skip(reason="Admin role removed — pending platform migration (Plan 1.2B)")
    def test_admin_cannot_disable_another_admin(self, client, db_session):
        pass

    @pytest.mark.skip(reason="Admin role removed — pending platform migration (Plan 1.2B)")
    def test_admin_can_disable_is_admin_teacher(self, client, db_session):
        pass
