import pytest
from datetime import datetime, timedelta
from tests.conftest import create_test_user, create_test_question, get_csrf_token, login_as, register_and_login, TestingSessionLocal
from app.models import User, ClassGroup, ClassMember, Favorite, Assignment, AssignmentRecord, Record, SiteConfig, Notification


class TestGuestExpiredLogin:
    def test_expired_guest_login_redirected(self, client, db_session):
        user = User(
            username="expiredguest",
            password_hash=User.hash_password("abc12345"),
            role="student",
            display_name="expiredguest",
            is_guest=True,
            guest_expires_at=datetime.now() - timedelta(hours=1),
        )
        db_session.add(user)
        db_session.commit()
        resp = login_as(client, "expiredguest", "abc12345")
        assert resp.status_code == 303
        assert "/student/guest-expired" in resp.headers.get("location", "")

    def test_active_guest_login_succeeds(self, client, db_session):
        user = User(
            username="activeguest",
            password_hash=User.hash_password("abc12345"),
            role="student",
            display_name="activeguest",
            is_guest=True,
            guest_expires_at=datetime.now() + timedelta(hours=1),
        )
        db_session.add(user)
        db_session.commit()
        resp = login_as(client, "activeguest", "abc12345")
        assert resp.status_code == 303
        assert resp.headers.get("location", "") == "/"

    def test_non_guest_login_unaffected(self, client, db_session):
        create_test_user(db_session, username="normalstudent")
        resp = login_as(client, "normalstudent", "abc12345")
        assert resp.status_code == 303
        assert resp.headers.get("location", "") == "/"


class TestAddMemberSyncClassId:
    @pytest.mark.skip(reason="Route changed (Plan 1.2B)")
    def test_add_member_updates_class_id(self, client, db_session):
        teacher = create_test_user(db_session, "addmemteacher", "teacher")
        student = create_test_user(db_session, "addmemstudent", "student")
        cls = ClassGroup(name="测试班", created_by=teacher.id)
        db_session.add(cls)
        db_session.commit()
        register_and_login(client, "addmemteacher", "teacher")
        csrf = get_csrf_token(client)
        client.post(f"/classes/{cls.id}/members/add", data={
            "username": "addmemstudent", "_csrf_token": csrf,
        })
        db_session.expire_all()
        updated = db_session.query(User).filter(User.username == "addmemstudent").first()
        assert updated.class_id == cls.id

    @pytest.mark.skip(reason="Route changed (Plan 1.2B)")
    def test_add_guest_member_clears_guest_status(self, client, db_session):
        teacher = create_test_user(db_session, "guestmemteacher", "teacher")
        guest = User(
            username="guestmemstudent",
            password_hash=User.hash_password("abc12345"),
            role="student",
            display_name="guestmemstudent",
            is_guest=True,
            guest_expires_at=datetime.now() + timedelta(hours=1),
        )
        db_session.add(guest)
        cls = ClassGroup(name="游客班", created_by=teacher.id)
        db_session.add(cls)
        db_session.commit()
        register_and_login(client, "guestmemteacher", "teacher")
        csrf = get_csrf_token(client)
        client.post(f"/classes/{cls.id}/members/add", data={
            "username": "guestmemstudent", "_csrf_token": csrf,
        })
        db_session.expire_all()
        updated = db_session.query(User).filter(User.username == "guestmemstudent").first()
        assert updated.is_guest is False
        assert updated.guest_expires_at is None
        assert updated.class_id == cls.id


class TestAssignmentGuestAccess:
    def test_expired_guest_cannot_see_assignments(self, client, db_session):
        user = User(
            username="guestassign",
            password_hash=User.hash_password("abc12345"),
            role="student",
            display_name="guestassign",
            is_guest=True,
            guest_expires_at=datetime.now() - timedelta(hours=1),
        )
        db_session.add(user)
        db_session.commit()
        login_as(client, "guestassign", "abc12345")
        resp = client.get("/student/assignments", follow_redirects=False)
        assert resp.status_code == 303
        assert "/student/guest-expired" in resp.headers.get("location", "")

    def test_expired_guest_cannot_complete_assignment(self, client, db_session):
        teacher = create_test_user(db_session, "assignteacher", "teacher")
        user = User(
            username="guestcomplete",
            password_hash=User.hash_password("abc12345"),
            role="student",
            display_name="guestcomplete",
            is_guest=True,
            guest_expires_at=datetime.now() - timedelta(hours=1),
        )
        db_session.add(user)
        assignment = Assignment(
            title="测试作业",
            question_ids="1",
            created_by=teacher.id,
        )
        db_session.add(assignment)
        db_session.commit()
        login_as(client, "guestcomplete", "abc12345")
        csrf = get_csrf_token(client)
        resp = client.post(f"/assignments/{assignment.id}/complete", data={
            "_csrf_token": csrf,
        }, follow_redirects=False)
        assert resp.status_code == 303
        assert "/student/guest-expired" in resp.headers.get("location", "")


class TestLeaderboardExcludesGuests:
    def test_guest_not_in_leaderboard(self, client, db_session):
        teacher = create_test_user(db_session, "lbteacher", "teacher")
        guest = User(
            username="lbguest",
            password_hash=User.hash_password("abc12345"),
            role="student",
            display_name="游客学生",
            is_guest=True,
            guest_expires_at=datetime.now() + timedelta(hours=1),
        )
        db_session.add(guest)
        q = create_test_question(db_session, created_by=teacher.id)
        db_session.add(Record(user_id=guest.id, question_id=q.id, user_answer="B", is_correct=True))
        db_session.commit()
        resp = client.get("/leaderboard", follow_redirects=True)
        assert "lbguest" not in resp.text

    def test_non_guest_student_in_leaderboard(self, client, db_session):
        teacher = create_test_user(db_session, "lbteacher2", "teacher")
        student = create_test_user(db_session, "lbstudent", "student")
        q = create_test_question(db_session, created_by=teacher.id)
        db_session.add(Record(user_id=student.id, question_id=q.id, user_answer="B", is_correct=True))
        db_session.commit()
        resp = client.get("/leaderboard", follow_redirects=True)
        assert "lbstudent" in resp.text


class TestRegisterInvalidClassId:
    def test_invalid_class_id_shows_error(self, client, db_session):
        csrf = get_csrf_token(client)
        resp = client.post("/register", data={
            "username": "badclassuser",
            "password": "abc12345",
            "role": "student",
            "display_name": "badclassuser",
            "join_mode": "formal",
            "class_id": "99999",
            "_csrf_token": csrf,
        }, follow_redirects=True)
        assert "所选班级不存在" in resp.text

    def test_no_class_creates_guest(self, client, db_session):
        csrf = get_csrf_token(client)
        resp = client.post("/register", data={
            "username": "noclassuser",
            "password": "abc12345",
            "role": "student",
            "display_name": "noclassuser",
            "join_mode": "guest",
            "_csrf_token": csrf,
        }, follow_redirects=True)
        db_session.expire_all()
        user = db_session.query(User).filter(User.username == "noclassuser").first()
        assert user is not None
        assert user.is_guest is True
        assert user.guest_expires_at is not None


class TestApproveStudentDuplicate:
    def test_cannot_approve_non_guest(self, client, db_session):
        teacher = create_test_user(db_session, "approveteacher", "teacher")
        student = create_test_user(db_session, "approvedstudent", "student")
        cls = ClassGroup(name="审批班", created_by=teacher.id)
        db_session.add(cls)
        db_session.commit()
        register_and_login(client, "approveteacher", "teacher")
        csrf = get_csrf_token(client)
        resp = client.post(f"/teacher/students/{student.id}/approve", data={
            "class_id": str(cls.id),
            "_csrf_token": csrf,
        }, follow_redirects=False)
        assert resp.status_code == 303
        db_session.expire_all()
        check = db_session.query(ClassMember).filter(
            ClassMember.class_id == cls.id, ClassMember.user_id == student.id
        ).first()
        assert check is None

    @pytest.mark.skip(reason="Route changed (Plan 1.2B)")
    def test_approve_guest_student(self, client, db_session):
        teacher = create_test_user(db_session, "approveteacher2", "teacher")
        guest = User(
            username="approveguest",
            password_hash=User.hash_password("abc12345"),
            role="student",
            display_name="approveguest",
            is_guest=True,
            guest_expires_at=datetime.now() + timedelta(hours=1),
        )
        db_session.add(guest)
        cls = ClassGroup(name="审批班2", created_by=teacher.id)
        db_session.add(cls)
        db_session.commit()
        register_and_login(client, "approveteacher2", "teacher")
        csrf = get_csrf_token(client)
        client.post(f"/teacher/students/{guest.id}/approve", data={
            "class_id": str(cls.id),
            "_csrf_token": csrf,
        })
        db_session.expire_all()
        updated = db_session.query(User).filter(User.username == "approveguest").first()
        assert updated.is_guest is False
        assert updated.class_id == cls.id
        notif = db_session.query(Notification).filter(Notification.user_id == guest.id).first()
        assert notif is not None
        assert "审核通过" in notif.title


class TestDeleteQuestionCascade:
    @pytest.mark.skip(reason="Route changed (Plan 1.2B)")
    def test_delete_question_removes_favorites(self, client, db_session):
        teacher = create_test_user(db_session, "delqteacher", "teacher")
        student = create_test_user(db_session, "delqstudent", "student")
        q = create_test_question(db_session, created_by=teacher.id)
        db_session.add(Favorite(user_id=student.id, question_id=q.id))
        db_session.commit()
        register_and_login(client, "delqteacher", "teacher")
        csrf = get_csrf_token(client)
        client.post(f"/teacher/questions/{q.id}/delete", data={"_csrf_token": csrf})
        remaining = db_session.query(Favorite).filter(Favorite.question_id == q.id).count()
        assert remaining == 0

    @pytest.mark.skip(reason="Route changed (Plan 1.2B)")
    def test_delete_question_removes_from_assignment(self, client, db_session):
        teacher = create_test_user(db_session, "delqteacher2", "teacher")
        q1 = create_test_question(db_session, content="Q1", created_by=teacher.id)
        q2 = create_test_question(db_session, content="Q2", created_by=teacher.id)
        q1_id = q1.id
        q2_id = q2.id
        assignment = Assignment(
            title="级联作业",
            question_ids=f"{q1_id},{q2_id}",
            created_by=teacher.id,
        )
        db_session.add(assignment)
        db_session.commit()
        register_and_login(client, "delqteacher2", "teacher")
        csrf = get_csrf_token(client)
        client.post(f"/teacher/questions/{q1_id}/delete", data={"_csrf_token": csrf})
        db_session.expire_all()
        updated = db_session.query(Assignment).filter(Assignment.id == assignment.id).first()
        assert str(q1_id) not in updated.question_ids
        assert str(q2_id) in updated.question_ids

    @pytest.mark.skip(reason="Route changed (Plan 1.2B)")
    def test_delete_question_removes_records(self, client, db_session):
        teacher = create_test_user(db_session, "delqteacher3", "teacher")
        student = create_test_user(db_session, "delqstudent3", "student")
        q = create_test_question(db_session, created_by=teacher.id)
        db_session.add(Record(user_id=student.id, question_id=q.id, user_answer="A", is_correct=False))
        db_session.commit()
        register_and_login(client, "delqteacher3", "teacher")
        csrf = get_csrf_token(client)
        client.post(f"/teacher/questions/{q.id}/delete", data={"_csrf_token": csrf})
        remaining = db_session.query(Record).filter(Record.question_id == q.id).count()
        assert remaining == 0


class TestRateLimitCaseInsensitive:
    def test_rate_limit_case_insensitive(self, client, db_session):
        create_test_user(db_session, username="CaseUser")
        for i in range(6):
            csrf = get_csrf_token(client)
            client.post("/login", data={
                "username": "CaseUser",
                "password": "wrongpass",
                "_csrf_token": csrf,
            }, follow_redirects=False)
        csrf = get_csrf_token(client)
        resp = client.post("/login", data={
            "username": "caseuser",
            "password": "abc12345",
            "_csrf_token": csrf,
        }, follow_redirects=False)
        assert resp.status_code == 429
