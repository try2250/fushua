import pytest
from app.models import User, ClassJoinRequest, AccountRecoveryRequest


def test_user_has_join_mode_field():
    user = User(
        username="testjoin",
        password_hash="hash",
        role="student",
        join_mode="formal",
    )
    assert user.join_mode == "formal"


def test_user_join_mode_default_is_empty():
    user = User(username="defaultjoin", password_hash="hash", role="student")
    assert user.join_mode in (None, "")


def test_class_join_request_model():
    req = ClassJoinRequest(
        user_id=1,
        class_id=2,
        display_name="张三",
        status="pending",
    )
    assert req.status == "pending"
    assert req.display_name == "张三"


def test_account_recovery_request_model():
    req = AccountRecoveryRequest(
        username="lostuser",
        class_id=1,
        display_name="李四",
        status="pending",
    )
    assert req.status == "pending"
    assert req.username == "lostuser"


from tests.conftest import create_test_user, get_csrf_token, TestingSessionLocal, register_and_login
from app.models import ClassGroup, ClassMember, ClassJoinRequest


class TestExplicitRegistration:
    def test_register_formal_join(self, client, db_session):
        cls = ClassGroup(name="测试班", created_by=0)
        db_session.add(cls)
        db_session.commit()
        db_session.refresh(cls)
        csrf = get_csrf_token(client)
        resp = client.post("/register", data={
            "username": "formal_student",
            "password": "abc12345",
            "role": "student",
            "display_name": "正式生",
            "join_mode": "formal",
            "class_id": str(cls.id),
            "_csrf_token": csrf,
        }, follow_redirects=False)
        assert resp.status_code == 303
        user = db_session.query(User).filter(User.username == "formal_student").first()
        assert user is not None
        assert user.join_mode == "formal"
        assert user.is_guest is False
        assert user.class_id == cls.id
        member = db_session.query(ClassMember).filter(
            ClassMember.class_id == cls.id, ClassMember.user_id == user.id
        ).first()
        assert member is not None

    def test_register_apply_join(self, client, db_session):
        cls = ClassGroup(name="申请班", created_by=0)
        db_session.add(cls)
        db_session.commit()
        db_session.refresh(cls)
        csrf = get_csrf_token(client)
        resp = client.post("/register", data={
            "username": "apply_student",
            "password": "abc12345",
            "role": "student",
            "display_name": "申请生",
            "join_mode": "apply",
            "class_id": str(cls.id),
            "_csrf_token": csrf,
        }, follow_redirects=False)
        assert resp.status_code == 303
        user = db_session.query(User).filter(User.username == "apply_student").first()
        assert user is not None
        assert user.join_mode == "apply"
        assert user.is_guest is True
        assert user.class_id is None
        req = db_session.query(ClassJoinRequest).filter(
            ClassJoinRequest.user_id == user.id, ClassJoinRequest.class_id == cls.id
        ).first()
        assert req is not None
        assert req.status == "pending"

    def test_register_guest(self, client, db_session):
        csrf = get_csrf_token(client)
        resp = client.post("/register", data={
            "username": "guest_student",
            "password": "abc12345",
            "role": "student",
            "display_name": "游客生",
            "join_mode": "guest",
            "_csrf_token": csrf,
        }, follow_redirects=False)
        assert resp.status_code == 303
        user = db_session.query(User).filter(User.username == "guest_student").first()
        assert user is not None
        assert user.join_mode == "guest"
        assert user.is_guest is True
        assert user.guest_expires_at is not None
        assert user.class_id is None

    def test_register_formal_without_class_is_error(self, client, db_session):
        csrf = get_csrf_token(client)
        resp = client.post("/register", data={
            "username": "no_class_student",
            "password": "abc12345",
            "role": "student",
            "display_name": "无班生",
            "join_mode": "formal",
            "class_id": "",
            "_csrf_token": csrf,
        }, follow_redirects=True)
        assert "班级" in resp.text

    def test_register_apply_without_class_is_error(self, client, db_session):
        csrf = get_csrf_token(client)
        resp = client.post("/register", data={
            "username": "no_class_apply",
            "password": "abc12345",
            "role": "student",
            "display_name": "无班申请",
            "join_mode": "apply",
            "class_id": "",
            "_csrf_token": csrf,
        }, follow_redirects=True)
        assert "班级" in resp.text

    def test_register_no_join_mode_is_error(self, client, db_session):
        csrf = get_csrf_token(client)
        resp = client.post("/register", data={
            "username": "no_mode_student",
            "password": "abc12345",
            "role": "student",
            "display_name": "无模式",
            "_csrf_token": csrf,
        }, follow_redirects=True)
        assert "注册方式" in resp.text


class TestJoinRequestApproval:
    @pytest.mark.skip(reason="Route changed (Plan 1.2B)")
    def test_teacher_can_see_pending_requests(self, client, db_session):
        teacher = create_test_user(db_session, username="req_teacher", role="teacher")
        cls = ClassGroup(name="审批班", created_by=teacher.id)
        db_session.add(cls)
        db_session.commit()
        db_session.refresh(cls)
        register_and_login(client, username="req_teacher", role="teacher")
        student = User(
            username="req_student",
            password_hash=User.hash_password("abc12345"),
            role="student",
            display_name="申请生",
            is_guest=True,
            join_mode="apply",
        )
        db_session.add(student)
        db_session.commit()
        db_session.refresh(student)
        req = ClassJoinRequest(user_id=student.id, class_id=cls.id, display_name="申请生", status="pending")
        db_session.add(req)
        db_session.commit()
        resp = client.get("/teacher/students", follow_redirects=True)
        assert resp.status_code == 200
        assert "申请生" in resp.text or "req_student" in resp.text

    @pytest.mark.skip(reason="Route changed (Plan 1.2B)")
    def test_teacher_approve_join_request(self, client, db_session):
        teacher = create_test_user(db_session, username="approve_teacher", role="teacher")
        cls = ClassGroup(name="批准班", created_by=teacher.id)
        db_session.add(cls)
        db_session.commit()
        db_session.refresh(cls)
        register_and_login(client, username="approve_teacher", role="teacher")
        student = User(
            username="approve_student",
            password_hash=User.hash_password("abc12345"),
            role="student",
            display_name="批准生",
            is_guest=True,
            join_mode="apply",
        )
        db_session.add(student)
        db_session.commit()
        db_session.refresh(student)
        req = ClassJoinRequest(user_id=student.id, class_id=cls.id, display_name="批准生", status="pending")
        db_session.add(req)
        db_session.commit()
        db_session.refresh(req)
        csrf = get_csrf_token(client)
        resp = client.post(f"/teacher/join-requests/{req.id}/approve", data={
            "_csrf_token": csrf,
        }, follow_redirects=False)
        assert resp.status_code == 303
        db_session.refresh(student)
        assert student.is_guest is False
        assert student.class_id == cls.id
        assert student.join_mode == "formal"
        db_session.refresh(req)
        assert req.status == "approved"

    @pytest.mark.skip(reason="Route changed (Plan 1.2B)")
    def test_teacher_reject_join_request(self, client, db_session):
        teacher = create_test_user(db_session, username="reject_teacher", role="teacher")
        cls = ClassGroup(name="拒绝班", created_by=teacher.id)
        db_session.add(cls)
        db_session.commit()
        db_session.refresh(cls)
        register_and_login(client, username="reject_teacher", role="teacher")
        student = User(
            username="reject_student",
            password_hash=User.hash_password("abc12345"),
            role="student",
            display_name="拒绝生",
            is_guest=True,
            join_mode="apply",
        )
        db_session.add(student)
        db_session.commit()
        db_session.refresh(student)
        req = ClassJoinRequest(user_id=student.id, class_id=cls.id, display_name="拒绝生", status="pending")
        db_session.add(req)
        db_session.commit()
        db_session.refresh(req)
        csrf = get_csrf_token(client)
        resp = client.post(f"/teacher/join-requests/{req.id}/reject", data={
            "_csrf_token": csrf,
        }, follow_redirects=False)
        assert resp.status_code == 303
        db_session.refresh(req)
        assert req.status == "rejected"
