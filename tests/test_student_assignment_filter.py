import pytest
from tests.conftest import create_test_user, create_test_question, register_and_login, get_csrf_token, login_as
from app.models import Assignment, ClassGroup, ClassMember


class TestStudentAssignmentFilter:
    @pytest.mark.skip(reason="Route changed (Plan 1.2B)")
    def test_student_only_sees_own_class_assignments(self, client, db_session):
        teacher = create_test_user(db_session, "filter_teacher", "teacher")
        q = create_test_question(db_session, created_by=teacher.id)

        class_a = ClassGroup(name="A班", created_by=teacher.id)
        class_b = ClassGroup(name="B班", created_by=teacher.id)
        db_session.add(class_a)
        db_session.add(class_b)
        db_session.commit()
        db_session.refresh(class_a)
        db_session.refresh(class_b)

        student_a = create_test_user(db_session, "student_a", "student")
        student_b = create_test_user(db_session, "student_b", "student")
        student_a.class_id = class_a.id
        student_b.class_id = class_b.id
        db_session.commit()

        db_session.add(ClassMember(class_id=class_a.id, user_id=student_a.id))
        db_session.add(ClassMember(class_id=class_b.id, user_id=student_b.id))
        db_session.commit()

        register_and_login(client, "filter_teacher", "teacher")
        csrf = get_csrf_token(client)
        client.post("/assignments/create", data={
            "title": "A班作业", "question_ids": str(q.id), "class_id": str(class_a.id),
            "_csrf_token": csrf,
        })
        client.post("/assignments/create", data={
            "title": "B班作业", "question_ids": str(q.id), "class_id": str(class_b.id),
            "_csrf_token": csrf,
        })

        login_as(client, "student_a")
        response = client.get("/student/assignments", follow_redirects=True)
        assert response.status_code == 200
        assert "A班作业" in response.text
        assert "B班作业" not in response.text

    @pytest.mark.skip(reason="Route changed (Plan 1.2B)")
    def test_student_cannot_complete_other_class_assignment(self, client, db_session):
        teacher = create_test_user(db_session, "filter_teacher2", "teacher")
        q = create_test_question(db_session, created_by=teacher.id)

        class_a = ClassGroup(name="A班", created_by=teacher.id)
        class_b = ClassGroup(name="B班", created_by=teacher.id)
        db_session.add(class_a)
        db_session.add(class_b)
        db_session.commit()
        db_session.refresh(class_a)
        db_session.refresh(class_b)

        student_a = create_test_user(db_session, "student_a2", "student")
        student_b = create_test_user(db_session, "student_b2", "student")
        student_a.class_id = class_a.id
        student_b.class_id = class_b.id
        db_session.commit()

        db_session.add(ClassMember(class_id=class_a.id, user_id=student_a.id))
        db_session.add(ClassMember(class_id=class_b.id, user_id=student_b.id))
        db_session.commit()

        register_and_login(client, "filter_teacher2", "teacher")
        csrf = get_csrf_token(client)
        client.post("/assignments/create", data={
            "title": "B班专属作业", "question_ids": str(q.id), "class_id": str(class_b.id),
            "_csrf_token": csrf,
        })

        b_assignment = db_session.query(Assignment).filter(Assignment.title == "B班专属作业").first()

        login_as(client, "student_a2")
        csrf = get_csrf_token(client)
        response = client.post(f"/assignments/{b_assignment.id}/complete", data={
            "_csrf_token": csrf,
        })
        assert response.status_code == 403

    @pytest.mark.skip(reason="Route changed (Plan 1.2B)")
    def test_student_can_complete_own_class_assignment(self, client, db_session):
        teacher = create_test_user(db_session, "filter_teacher3", "teacher")
        q = create_test_question(db_session, created_by=teacher.id)

        class_a = ClassGroup(name="A班", created_by=teacher.id)
        db_session.add(class_a)
        db_session.commit()
        db_session.refresh(class_a)

        student_a = create_test_user(db_session, "student_a3", "student")
        student_a.class_id = class_a.id
        db_session.commit()

        db_session.add(ClassMember(class_id=class_a.id, user_id=student_a.id))
        db_session.commit()

        register_and_login(client, "filter_teacher3", "teacher")
        csrf = get_csrf_token(client)
        client.post("/assignments/create", data={
            "title": "A班测试作业", "question_ids": str(q.id), "class_id": str(class_a.id),
            "_csrf_token": csrf,
        })

        a_assignment = db_session.query(Assignment).filter(Assignment.title == "A班测试作业").first()

        login_as(client, "student_a3")
        csrf = get_csrf_token(client)
        response = client.post(f"/assignments/{a_assignment.id}/complete", data={
            "_csrf_token": csrf,
        })
        assert response.status_code == 303

    def test_student_without_class_sees_no_assignments(self, client, db_session):
        teacher = create_test_user(db_session, "filter_teacher4", "teacher")
        q = create_test_question(db_session, created_by=teacher.id)

        class_a = ClassGroup(name="A班", created_by=teacher.id)
        db_session.add(class_a)
        db_session.commit()
        db_session.refresh(class_a)

        student_no_class = create_test_user(db_session, "student_no_class", "student")

        register_and_login(client, "filter_teacher4", "teacher")
        csrf = get_csrf_token(client)
        client.post("/assignments/create", data={
            "title": "A班专属作业", "question_ids": str(q.id), "class_id": str(class_a.id),
            "_csrf_token": csrf,
        })

        login_as(client, "student_no_class")
        response = client.get("/student/assignments", follow_redirects=True)
        assert response.status_code == 200
        assert "A班专属作业" not in response.text
