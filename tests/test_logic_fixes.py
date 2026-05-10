import pytest
from tests.conftest import create_test_user, get_csrf_token, register_and_login
from app.models import User, ClassGroup, ClassMember


class TestTeacherRequireAdminConsistency:
    def test_teacher_require_admin_rejects_is_admin_teacher(self, client, db_session):
        teacher = create_test_user(db_session, username="isadmin_teacher", role="teacher")
        teacher.is_admin = True
        db_session.commit()
        from app.routers.teacher import require_admin
        from fastapi import HTTPException
        request = type("Request", (), {"session": {"user_id": teacher.id}})()
        with pytest.raises(HTTPException) as exc_info:
            require_admin(request, db_session)
        assert exc_info.value.status_code == 403


class TestAddMemberUpdatesJoinMode:
    def test_add_member_clears_guest_status(self, client, db_session):
        teacher = create_test_user(db_session, username="addmem_teacher", role="teacher")
        cls = ClassGroup(name="添加成员班", created_by=teacher.id)
        db_session.add(cls)
        db_session.commit()
        db_session.refresh(cls)
        student = User(
            username="addmem_student",
            password_hash=User.hash_password("abc12345"),
            role="student",
            display_name="添加成员生",
            is_guest=True,
            join_mode="guest",
        )
        db_session.add(student)
        db_session.commit()
        db_session.refresh(student)
        register_and_login(client, username="addmem_teacher", role="teacher")
        csrf = get_csrf_token(client)
        resp = client.post(f"/classes/{cls.id}/members/add", data={
            "username": "addmem_student",
            "_csrf_token": csrf,
        }, follow_redirects=False)
        assert resp.status_code == 303
        db_session.refresh(student)
        assert student.is_guest is False
        assert student.join_mode == "formal"
        assert student.guest_expires_at is None


class TestAdminCannotDisableAdmin:
    def test_admin_cannot_disable_another_admin(self, client, db_session):
        admin = create_test_user(db_session, username="nodis_admin", role="admin")
        other_admin = create_test_user(db_session, username="nodis_other", role="admin")
        db_session.commit()
        register_and_login(client, username="nodis_admin", role="admin")
        csrf = get_csrf_token(client)
        resp = client.post(f"/admin/users/{other_admin.id}/toggle-disable", data={
            "_csrf_token": csrf,
        }, follow_redirects=False)
        assert resp.status_code == 403

    def test_admin_can_disable_is_admin_teacher(self, client, db_session):
        admin = create_test_user(db_session, username="candis_admin", role="admin")
        teacher = create_test_user(db_session, username="candis_teacher", role="teacher")
        teacher.is_admin = True
        db_session.commit()
        register_and_login(client, username="candis_admin", role="admin")
        csrf = get_csrf_token(client)
        resp = client.post(f"/admin/users/{teacher.id}/toggle-disable", data={
            "_csrf_token": csrf,
        }, follow_redirects=False)
        assert resp.status_code == 303
        db_session.refresh(teacher)
        assert teacher.is_disabled is True
