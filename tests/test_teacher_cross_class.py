import pytest
from tests.conftest import (
    create_test_user,
    create_test_question,
    register_and_login,
    login_as,
    get_csrf_token,
)
from app.models import ClassGroup, ClassMember


def create_test_class(db, name, created_by):
    cls = ClassGroup(name=name, created_by=created_by)
    db.add(cls)
    db.commit()
    db.refresh(cls)
    return cls


def add_student_to_class(db, student_id, class_id):
    member = ClassMember(class_id=class_id, user_id=student_id)
    db.add(member)
    db.commit()


class TestTeacherCrossClassAccess:
    def test_teacher_cannot_view_other_class_student_detail(self, client, db_session):
        teacher_a = create_test_user(db_session, "teacher_a", "teacher")
        teacher_b = create_test_user(db_session, "teacher_b", "teacher")
        student_a = create_test_user(db_session, "student_a", "student")
        student_b = create_test_user(db_session, "student_b", "student")

        class_a = create_test_class(db_session, "Class A", teacher_a.id)
        class_b = create_test_class(db_session, "Class B", teacher_b.id)

        add_student_to_class(db_session, student_a.id, class_a.id)
        add_student_to_class(db_session, student_b.id, class_b.id)

        register_and_login(client, "teacher_a", "teacher")
        response = client.get(f"/teacher/students/{student_b.id}")
        assert response.status_code == 404

    def test_teacher_cannot_view_other_class_student_pdf(self, client, db_session):
        teacher_a = create_test_user(db_session, "teacher_a2", "teacher")
        teacher_b = create_test_user(db_session, "teacher_b2", "teacher")
        student_a = create_test_user(db_session, "student_a2", "student")
        student_b = create_test_user(db_session, "student_b2", "student")

        class_a = create_test_class(db_session, "Class A2", teacher_a.id)
        class_b = create_test_class(db_session, "Class B2", teacher_b.id)

        add_student_to_class(db_session, student_a.id, class_a.id)
        add_student_to_class(db_session, student_b.id, class_b.id)

        register_and_login(client, "teacher_a2", "teacher")
        response = client.get(f"/teacher/students/{student_b.id}/export/pdf")
        assert response.status_code == 404

    def test_teacher_cannot_view_other_class_parent_report(self, client, db_session):
        teacher_a = create_test_user(db_session, "teacher_a3", "teacher")
        teacher_b = create_test_user(db_session, "teacher_b3", "teacher")
        student_a = create_test_user(db_session, "student_a3", "student")
        student_b = create_test_user(db_session, "student_b3", "student")

        class_a = create_test_class(db_session, "Class A3", teacher_a.id)
        class_b = create_test_class(db_session, "Class B3", teacher_b.id)

        add_student_to_class(db_session, student_a.id, class_a.id)
        add_student_to_class(db_session, student_b.id, class_b.id)

        register_and_login(client, "teacher_a3", "teacher")
        response = client.get(f"/teacher/students/{student_b.id}/parent-report")
        assert response.status_code == 404

    def test_teacher_can_view_own_class_student_detail(self, client, db_session):
        teacher_a = create_test_user(db_session, "teacher_a4", "teacher")
        student_a = create_test_user(db_session, "student_a4", "student")

        class_a = create_test_class(db_session, "Class A4", teacher_a.id)
        add_student_to_class(db_session, student_a.id, class_a.id)

        register_and_login(client, "teacher_a4", "teacher")
        response = client.get(f"/teacher/students/{student_a.id}")
        assert response.status_code == 200

    def test_teacher_cannot_view_nonexistent_student(self, client, db_session):
        teacher_a = create_test_user(db_session, "teacher_a5", "teacher")
        register_and_login(client, "teacher_a5", "teacher")
        response = client.get("/teacher/students/99999")
        assert response.status_code == 404
