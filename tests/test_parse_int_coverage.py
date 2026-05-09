import pytest
from tests.conftest import create_test_user, create_test_question, login_as, register_and_login


class TestParseIntCoverage:
    def test_teacher_create_question_invalid_difficulty_no_500(self, client, db_session):
        teacher = create_test_user(db_session, username="teacher1", role="teacher")
        login_as(client, "teacher1")
        csrf = __import__("tests.conftest", fromlist=["get_csrf_token"]).get_csrf_token(client)

        response = client.post("/teacher/questions/create", data={
            "subject": "数学",
            "content": "1+1=?",
            "answer": "B",
            "difficulty": "invalid",
            "q_type": "choice",
            "_csrf_token": csrf,
        })
        assert response.status_code != 500
        if response.status_code == 303:
            assert "/teacher/questions/create" not in response.headers.get("location", "")

    def test_teacher_create_question_difficulty_out_of_range_no_500(self, client, db_session):
        teacher = create_test_user(db_session, username="teacher2", role="teacher")
        login_as(client, "teacher2")
        csrf = __import__("tests.conftest", fromlist=["get_csrf_token"]).get_csrf_token(client)

        response = client.post("/teacher/questions/create", data={
            "subject": "数学",
            "content": "1+1=?",
            "answer": "B",
            "difficulty": "99",
            "q_type": "choice",
            "_csrf_token": csrf,
        })
        assert response.status_code != 500

    def test_teacher_edit_question_invalid_difficulty_no_500(self, client, db_session):
        teacher = create_test_user(db_session, username="teacher3", role="teacher")
        question = create_test_question(db_session, created_by=teacher.id)
        login_as(client, "teacher3")
        csrf = __import__("tests.conftest", fromlist=["get_csrf_token"]).get_csrf_token(client)

        response = client.post(f"/teacher/questions/{question.id}/edit", data={
            "subject": "数学",
            "content": "1+1=?",
            "answer": "B",
            "difficulty": "abc",
            "q_type": "choice",
            "_csrf_token": csrf,
        })
        assert response.status_code != 500

    def test_teacher_create_question_invalid_bank_id_no_500(self, client, db_session):
        teacher = create_test_user(db_session, username="teacher4", role="teacher")
        login_as(client, "teacher4")
        csrf = __import__("tests.conftest", fromlist=["get_csrf_token"]).get_csrf_token(client)

        response = client.post("/teacher/questions/create", data={
            "subject": "数学",
            "content": "1+1=?",
            "answer": "B",
            "difficulty": "2",
            "q_type": "choice",
            "bank_id": "not_a_number",
            "_csrf_token": csrf,
        })
        assert response.status_code != 500

    def test_student_submit_practice_invalid_question_id_no_500(self, client, db_session):
        student = create_test_user(db_session, username="student1")
        login_as(client, "student1")
        csrf = __import__("tests.conftest", fromlist=["get_csrf_token"]).get_csrf_token(client)

        response = client.post("/student/practice/submit", data={
            "answer_invalidid": "A",
            "_csrf_token": csrf,
        })
        assert response.status_code != 500

    def test_student_create_plan_invalid_daily_goal_no_500(self, client, db_session):
        student = create_test_user(db_session, username="student2")
        login_as(client, "student2")
        csrf = __import__("tests.conftest", fromlist=["get_csrf_token"]).get_csrf_token(client)

        response = client.post("/student/plans/create", data={
            "subject": "数学",
            "semester": "八年级上册",
            "daily_goal": "xyz",
            "_csrf_token": csrf,
        })
        assert response.status_code != 500
