import pytest
from tests.conftest import create_test_user, get_csrf_token, TestingSessionLocal, register_and_login
from app.models import User, ClassGroup, ClassMember, AccountRecoveryRequest


class TestAccountRecovery:
    def test_recover_page_renders(self, client):
        resp = client.get("/recover", follow_redirects=True)
        assert resp.status_code == 200
        assert "找回" in resp.text

    def test_recover_submit_creates_request(self, client, db_session):
        cls = ClassGroup(name="找回班", created_by=0)
        db_session.add(cls)
        db_session.commit()
        db_session.refresh(cls)
        user = create_test_user(db_session, username="recover_user")
        db_session.add(ClassMember(class_id=cls.id, user_id=user.id))
        user.class_id = cls.id
        db_session.commit()
        csrf = get_csrf_token(client)
        resp = client.post("/recover", data={
            "username": "recover_user",
            "class_id": str(cls.id),
            "display_name": user.display_name,
            "_csrf_token": csrf,
        }, follow_redirects=True)
        assert resp.status_code == 200
        req = db_session.query(AccountRecoveryRequest).filter(
            AccountRecoveryRequest.username == "recover_user"
        ).first()
        assert req is not None
        assert req.status == "pending"
        assert req.class_id == cls.id

    def test_recover_nonexistent_user_still_submits(self, client, db_session):
        csrf = get_csrf_token(client)
        resp = client.post("/recover", data={
            "username": "nonexistent_user",
            "class_id": "",
            "display_name": "某人",
            "_csrf_token": csrf,
        }, follow_redirects=True)
        assert resp.status_code == 200

    def test_recover_empty_username_is_error(self, client, db_session):
        csrf = get_csrf_token(client)
        resp = client.post("/recover", data={
            "username": "",
            "class_id": "",
            "display_name": "",
            "_csrf_token": csrf,
        }, follow_redirects=True)
        assert "用户名" in resp.text

    def test_login_page_has_recover_link(self, client):
        resp = client.get("/login", follow_redirects=True)
        assert "找回" in resp.text or "recover" in resp.text


class TestRecoveryApproval:
    @pytest.mark.skip(reason="Admin role removed — recovery routes pending platform migration (Plan 1.2B)")
    def test_admin_can_see_recovery_requests(self, client, db_session):
        admin = create_test_user(db_session, username="rec_admin", role="admin", password="abc12345")
        db_session.commit()
        recovery = AccountRecoveryRequest(username="lost_student", display_name="丢失生", status="pending")
        db_session.add(recovery)
        db_session.commit()
        register_and_login(client, username="rec_admin", role="admin")
        resp = client.get("/admin/recovery-requests", follow_redirects=True)
        assert resp.status_code == 200
        assert "lost_student" in resp.text

    @pytest.mark.skip(reason="Admin role removed (Plan 1.2B)")
    def test_admin_approve_recovery_resets_password(self, client, db_session):
        admin = create_test_user(db_session, username="reset_admin", role="admin", password="abc12345")
        db_session.commit()
        student = create_test_user(db_session, username="reset_student")
        old_hash = student.password_hash
        recovery = AccountRecoveryRequest(username="reset_student", display_name="重置生", status="pending")
        db_session.add(recovery)
        db_session.commit()
        db_session.refresh(recovery)
        register_and_login(client, username="reset_admin", role="admin")
        csrf = get_csrf_token(client)
        resp = client.post(f"/admin/recovery-requests/{recovery.id}/approve", data={
            "_csrf_token": csrf,
        }, follow_redirects=False)
        assert resp.status_code == 303
        db_session.refresh(student)
        assert student.password_hash != old_hash
        assert User.verify_password(student.password_hash, "abc12345")
        db_session.refresh(recovery)
        assert recovery.status == "approved"

    @pytest.mark.skip(reason="Admin role removed (Plan 1.2B)")
    def test_admin_reject_recovery(self, client, db_session):
        admin = create_test_user(db_session, username="rej_admin", role="admin", password="abc12345")
        db_session.commit()
        recovery = AccountRecoveryRequest(username="rej_student", display_name="拒绝生", status="pending")
        db_session.add(recovery)
        db_session.commit()
        db_session.refresh(recovery)
        register_and_login(client, username="rej_admin", role="admin")
        csrf = get_csrf_token(client)
        resp = client.post(f"/admin/recovery-requests/{recovery.id}/reject", data={
            "_csrf_token": csrf,
        }, follow_redirects=False)
        assert resp.status_code == 303
        db_session.refresh(recovery)
        assert recovery.status == "rejected"

    def test_teacher_can_see_class_recovery_requests(self, client, db_session):
        teacher = create_test_user(db_session, username="cls_rec_teacher", role="teacher")
        cls = ClassGroup(name="找回审批班", created_by=teacher.id)
        db_session.add(cls)
        db_session.commit()
        db_session.refresh(cls)
        register_and_login(client, username="cls_rec_teacher", role="teacher")
        recovery = AccountRecoveryRequest(username="cls_lost_student", class_id=cls.id, display_name="班级找回生", status="pending")
        db_session.add(recovery)
        db_session.commit()
        resp = client.get("/teacher/students", follow_redirects=True)
        assert resp.status_code == 200
