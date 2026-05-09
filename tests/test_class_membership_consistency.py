import pytest
from app.models import ClassGroup, ClassMember, User
from tests.conftest import create_test_user, register_and_login, login_as, get_csrf_token


def create_test_class(db, name="测试班级", created_by=1):
    cls = ClassGroup(name=name, created_by=created_by)
    db.add(cls)
    db.commit()
    db.refresh(cls)
    return cls


class TestRemoveMemberClearsClassId:
    def test_remove_member_clears_user_class_id(self, client, db_session):
        teacher = create_test_user(db_session, username="teacher_test", role="teacher")
        student = create_test_user(db_session, username="student_remove", role="student")
        cls = create_test_class(db_session, name="移除测试班级", created_by=teacher.id)

        register_and_login(client, "teacher_test", role="teacher")

        db_session.add(ClassMember(class_id=cls.id, user_id=student.id))
        student.class_id = cls.id
        db_session.commit()

        csrf = get_csrf_token(client)
        response = client.post(
            f"/classes/{cls.id}/members/{student.id}/remove",
            data={"_csrf_token": csrf},
            follow_redirects=False,
        )
        assert response.status_code == 303

        db_session.expire_all()
        updated_student = db_session.query(User).filter(User.id == student.id).first()
        assert updated_student.class_id is None

        member_exists = db_session.query(ClassMember).filter(
            ClassMember.class_id == cls.id, ClassMember.user_id == student.id
        ).first()
        assert member_exists is None

    def test_remove_from_other_class_does_not_clear_class_id(self, client, db_session):
        teacher = create_test_user(db_session, username="teacher_test2", role="teacher")
        student = create_test_user(db_session, username="student_other_class", role="student")
        cls1 = create_test_class(db_session, name="班级1", created_by=teacher.id)
        cls2 = create_test_class(db_session, name="班级2", created_by=teacher.id)

        register_and_login(client, "teacher_test2", role="teacher")

        db_session.add(ClassMember(class_id=cls1.id, user_id=student.id))
        student.class_id = cls1.id
        db_session.commit()

        csrf = get_csrf_token(client)
        client.post(
            f"/classes/{cls2.id}/members/{student.id}/remove",
            data={"_csrf_token": csrf},
            follow_redirects=False,
        )

        db_session.expire_all()
        updated_student = db_session.query(User).filter(User.id == student.id).first()
        assert updated_student.class_id == cls1.id


class TestAddMemberChecksExistingClass:
    def test_add_student_already_in_other_class_returns_error(self, client, db_session):
        teacher = create_test_user(db_session, username="teacher_test3", role="teacher")
        student = create_test_user(db_session, username="student_other_class2", role="student")
        cls1 = create_test_class(db_session, name="班级A", created_by=teacher.id)
        cls2 = create_test_class(db_session, name="班级B", created_by=teacher.id)

        register_and_login(client, "teacher_test3", role="teacher")

        db_session.add(ClassMember(class_id=cls1.id, user_id=student.id))
        student.class_id = cls1.id
        db_session.commit()

        csrf = get_csrf_token(client)
        response = client.post(
            f"/classes/{cls2.id}/members/add",
            data={"username": "student_other_class2", "_csrf_token": csrf},
            follow_redirects=False,
        )

        assert response.status_code == 200
        assert "已在其他班级".encode() in response.content

        member_in_cls2 = db_session.query(ClassMember).filter(
            ClassMember.class_id == cls2.id, ClassMember.user_id == student.id
        ).first()
        assert member_in_cls2 is None

    def test_add_student_without_class_id_succeeds(self, client, db_session):
        teacher = create_test_user(db_session, username="teacher_test4", role="teacher")
        student = create_test_user(db_session, username="student_no_class", role="student")
        cls = create_test_class(db_session, name="新班级", created_by=teacher.id)

        register_and_login(client, "teacher_test4", role="teacher")

        assert student.class_id is None

        csrf = get_csrf_token(client)
        response = client.post(
            f"/classes/{cls.id}/members/add",
            data={"username": "student_no_class", "_csrf_token": csrf},
            follow_redirects=False,
        )

        assert response.status_code == 303

        member = db_session.query(ClassMember).filter(
            ClassMember.class_id == cls.id, ClassMember.user_id == student.id
        ).first()
        assert member is not None

        db_session.expire_all()
        updated_student = db_session.query(User).filter(User.id == student.id).first()
        assert updated_student.class_id == cls.id

    def test_add_student_to_same_class_succeeds(self, client, db_session):
        teacher = create_test_user(db_session, username="teacher_test5", role="teacher")
        student = create_test_user(db_session, username="student_same_class", role="student")
        cls = create_test_class(db_session, name="同一班级", created_by=teacher.id)

        register_and_login(client, "teacher_test5", role="teacher")

        db_session.add(ClassMember(class_id=cls.id, user_id=student.id))
        student.class_id = cls.id
        db_session.commit()

        csrf = get_csrf_token(client)
        response = client.post(
            f"/classes/{cls.id}/members/add",
            data={"username": "student_same_class", "_csrf_token": csrf},
            follow_redirects=False,
        )

        assert response.status_code == 303

        members_count = db_session.query(ClassMember).filter(
            ClassMember.class_id == cls.id, ClassMember.user_id == student.id
        ).count()
        assert members_count == 1
