import pytest
from app.models import ClassGroup, ClassMember, User, ClassJoinRequest
from tests.conftest import create_test_user, register_and_login, get_csrf_token


def create_test_class(db, name="测试班级", created_by=1):
    cls = ClassGroup(name=name, created_by=created_by)
    db.add(cls)
    db.commit()
    db.refresh(cls)
    return cls


class TestBulkImportConsistency:
    """Test that bulk import respects class membership consistency"""

    @pytest.mark.skip(reason="Route changed (Plan 1.2B)")
    def test_import_student_already_in_other_class_skips(self, client, db_session):
        """Student in class 1 cannot be imported into class 2"""
        teacher_a = create_test_user(db_session, username="teacherA_import", role="teacher")
        teacher_b = create_test_user(db_session, username="teacherB_import", role="teacher")
        student = create_test_user(db_session, username="student_import1", role="student")

        cls1 = create_test_class(db_session, name="班级1", created_by=teacher_a.id)
        cls2 = create_test_class(db_session, name="班级2", created_by=teacher_b.id)

        db_session.add(ClassMember(class_id=cls1.id, user_id=student.id))
        student.class_id = cls1.id
        db_session.commit()

        register_and_login(client, "teacherB_import", role="teacher")
        csrf = get_csrf_token(client)

        csv_content = "username,display_name\nstudent_import1,学生1"

        response = client.post(
            f"/teacher/classes/{cls2.id}/import-students",
            data={"csv_text": csv_content, "_csrf_token": csrf},
        )

        assert response.status_code == 200

        db_session.expire_all()
        updated_student = db_session.query(User).filter(User.id == student.id).first()
        assert updated_student.class_id == cls1.id

        member_in_cls2 = db_session.query(ClassMember).filter(
            ClassMember.class_id == cls2.id, ClassMember.user_id == student.id
        ).first()
        assert member_in_cls2 is None

    @pytest.mark.skip(reason="Route changed (Plan 1.2B)")
    def test_import_student_without_class_succeeds(self, client, db_session):
        """Student without class can be imported"""
        teacher = create_test_user(db_session, username="teacher_import2", role="teacher")
        student = create_test_user(db_session, username="student_import2", role="student")
        cls = create_test_class(db_session, name="导入班级", created_by=teacher.id)

        assert student.class_id is None

        register_and_login(client, "teacher_import2", role="teacher")
        csrf = get_csrf_token(client)

        csv_content = "username,display_name\nstudent_import2,学生2"

        response = client.post(
            f"/teacher/classes/{cls.id}/import-students",
            data={"csv_text": csv_content, "_csrf_token": csrf},
        )

        assert response.status_code == 200

        db_session.expire_all()
        updated_student = db_session.query(User).filter(User.id == student.id).first()
        assert updated_student.class_id == cls.id

        member = db_session.query(ClassMember).filter(
            ClassMember.class_id == cls.id, ClassMember.user_id == student.id
        ).first()
        assert member is not None

    @pytest.mark.skip(reason="Route changed (Plan 1.2B)")
    def test_import_student_already_in_target_class_idempotent(self, client, db_session):
        """Importing student already in target class is idempotent"""
        teacher = create_test_user(db_session, username="teacher_import3", role="teacher")
        student = create_test_user(db_session, username="student_import3", role="student")
        cls = create_test_class(db_session, name="目标班级", created_by=teacher.id)

        db_session.add(ClassMember(class_id=cls.id, user_id=student.id))
        student.class_id = cls.id
        db_session.commit()

        register_and_login(client, "teacher_import3", role="teacher")
        csrf = get_csrf_token(client)

        csv_content = "username,display_name\nstudent_import3,学生3"

        response = client.post(
            f"/teacher/classes/{cls.id}/import-students",
            data={"csv_text": csv_content, "_csrf_token": csrf},
        )

        assert response.status_code == 200

        db_session.expire_all()
        updated_student = db_session.query(User).filter(User.id == student.id).first()
        assert updated_student.class_id == cls.id

        members_count = db_session.query(ClassMember).filter(
            ClassMember.class_id == cls.id, ClassMember.user_id == student.id
        ).count()
        assert members_count == 1


class TestApprovalConsistency:
    """Test that approval endpoints respect class membership consistency"""

    def test_approve_guest_already_in_other_class_fails(self, client, db_session):
        """Cannot approve guest who is already in another class"""
        teacher_a = create_test_user(db_session, username="teacherA_approve", role="teacher")
        teacher_b = create_test_user(db_session, username="teacherB_approve", role="teacher")
        student = create_test_user(db_session, username="guest_approve1", role="student")

        cls1 = create_test_class(db_session, name="班级A", created_by=teacher_a.id)
        cls2 = create_test_class(db_session, name="班级B", created_by=teacher_b.id)

        student.is_guest = True
        student.class_id = cls1.id
        db_session.commit()

        register_and_login(client, "teacherB_approve", role="teacher")
        csrf = get_csrf_token(client)

        response = client.post(
            f"/teacher/students/{student.id}/approve",
            data={"class_id": str(cls2.id), "_csrf_token": csrf},
            follow_redirects=False,
        )

        assert response.status_code == 303

        db_session.expire_all()
        updated_student = db_session.query(User).filter(User.id == student.id).first()
        assert updated_student.class_id == cls1.id

        member_in_cls2 = db_session.query(ClassMember).filter(
            ClassMember.class_id == cls2.id, ClassMember.user_id == student.id
        ).first()
        assert member_in_cls2 is None

    def test_approve_join_request_already_in_other_class_fails(self, client, db_session):
        """Cannot approve join request if student is already in another class"""
        teacher_a = create_test_user(db_session, username="teacherA_join", role="teacher")
        teacher_b = create_test_user(db_session, username="teacherB_join", role="teacher")
        student = create_test_user(db_session, username="student_join1", role="student")

        cls1 = create_test_class(db_session, name="班级X", created_by=teacher_a.id)
        cls2 = create_test_class(db_session, name="班级Y", created_by=teacher_b.id)

        student.class_id = cls1.id
        db_session.add(ClassMember(class_id=cls1.id, user_id=student.id))
        db_session.commit()

        join_req = ClassJoinRequest(
            user_id=student.id,
            class_id=cls2.id,
            status="pending"
        )
        db_session.add(join_req)
        db_session.commit()
        db_session.refresh(join_req)

        register_and_login(client, "teacherB_join", role="teacher")
        csrf = get_csrf_token(client)

        response = client.post(
            f"/teacher/join-requests/{join_req.id}/approve",
            data={"_csrf_token": csrf},
            follow_redirects=False,
        )

        assert response.status_code == 303

        db_session.expire_all()
        updated_student = db_session.query(User).filter(User.id == student.id).first()
        assert updated_student.class_id == cls1.id

        member_in_cls2 = db_session.query(ClassMember).filter(
            ClassMember.class_id == cls2.id, ClassMember.user_id == student.id
        ).first()
        assert member_in_cls2 is None

        updated_req = db_session.query(ClassJoinRequest).filter(
            ClassJoinRequest.id == join_req.id
        ).first()
        assert updated_req.status == "pending"
