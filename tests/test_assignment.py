from tests.conftest import create_test_user, create_test_question, register_and_login, get_csrf_token
from app.models import Assignment


class TestAssignment:
    def test_teacher_create_assignment(self, client, db_session):
        teacher = create_test_user(db_session, "assteacher", "teacher")
        q = create_test_question(db_session, created_by=teacher.id)
        register_and_login(client, "assteacher", "teacher")
        csrf = get_csrf_token(client)
        response = client.post("/assignments/create", data={
            "title": "第一次作业", "description": "完成以下题目",
            "question_ids": str(q.id), "deadline": "2026-06-01",
            "_csrf_token": csrf,
        })
        assert response.status_code == 303
        a = db_session.query(Assignment).first()
        assert a is not None
        assert a.title == "第一次作业"

    def test_teacher_see_assignments(self, client, db_session):
        teacher = create_test_user(db_session, "assteacher2", "teacher")
        q = create_test_question(db_session, created_by=teacher.id)
        register_and_login(client, "assteacher2", "teacher")
        csrf = get_csrf_token(client)
        client.post("/assignments/create", data={
            "title": "作业1", "question_ids": str(q.id), "deadline": "2026-06-01",
            "_csrf_token": csrf,
        })
        response = client.get("/teacher/assignments", follow_redirects=True)
        assert response.status_code == 200
        assert "作业1" in response.text

    def test_student_see_assignments(self, client, db_session):
        teacher = create_test_user(db_session, "assteacher3", "teacher")
        q = create_test_question(db_session, created_by=teacher.id)
        register_and_login(client, "assteacher3", "teacher")
        csrf = get_csrf_token(client)
        client.post("/assignments/create", data={
            "title": "学生作业", "question_ids": str(q.id), "deadline": "2026-06-01",
            "_csrf_token": csrf,
        })
        register_and_login(client, "assstudent", "student")
        response = client.get("/student/assignments", follow_redirects=True)
        assert response.status_code == 200
        assert "学生作业" in response.text
