from tests.conftest import (
    create_test_user, create_test_question,
    register_and_login, login_as, get_csrf_token,
)
from app.models import User, Question


class TestRegisterLoginFlow:
    def test_register_auto_login_redirect(self, client, db_session):
        response = client.post("/register", data={
            "username": "newuser",
            "password": "abc12345",
            "role": "student",
            "display_name": "NewUser",
            "join_mode": "guest",
            "_csrf_token": get_csrf_token(client),
        })
        assert response.status_code == 303
        assert response.headers["location"] == "/"
        user = db_session.query(User).filter(User.username == "newuser").first()
        assert user is not None

    def test_login_redirect_to_home(self, client, db_session):
        create_test_user(db_session, "loginuser", "student")
        response = login_as(client, "loginuser")
        assert response.status_code == 303
        assert response.headers["location"] == "/"

    def test_homepage_shows_user_info_after_login(self, client, db_session):
        register_and_login(client, "homeuser", "student")
        response = client.get("/", follow_redirects=True)
        assert response.status_code == 200
        assert "homeuser" in response.text

    def test_logout_clears_session(self, client, db_session):
        register_and_login(client, "logoutuser", "student")
        response = client.post("/logout")
        assert response.status_code == 303
        response = client.get("/", follow_redirects=True)
        assert "登录" in response.text


class TestStudentPracticeFlow:
    def test_practice_page_has_csrf(self, client, db_session):
        teacher = create_test_user(db_session, "teacher1", "teacher")
        create_test_question(db_session, created_by=teacher.id)
        register_and_login(client, "pracuser", "student")
        response = client.get("/student/practice", follow_redirects=True)
        assert response.status_code == 200
        assert "_csrf_token" in response.text

    def test_submit_practice_shows_continue_button(self, client, db_session):
        teacher = create_test_user(db_session, "teacher2", "teacher")
        q = create_test_question(db_session, created_by=teacher.id)
        register_and_login(client, "submituser", "student")
        csrf = get_csrf_token(client)
        response = client.post("/student/practice/submit", data={
            f"answer_{q.id}": "B",
            "_csrf_token": csrf,
        }, follow_redirects=True)
        assert response.status_code == 200
        assert "继续刷题" in response.text or "再刷一组" in response.text

    def test_submit_practice_shows_accuracy(self, client, db_session):
        teacher = create_test_user(db_session, "teacher3", "teacher")
        q = create_test_question(db_session, created_by=teacher.id)
        register_and_login(client, "accuser", "student")
        csrf = get_csrf_token(client)
        response = client.post("/student/practice/submit", data={
            f"answer_{q.id}": "B",
            "_csrf_token": csrf,
        }, follow_redirects=True)
        assert response.status_code == 200
        assert "正确率" in response.text or "100" in response.text

    def test_practice_with_subject_filter(self, client, db_session):
        teacher = create_test_user(db_session, "teacher4", "teacher")
        create_test_question(db_session, subject="数学", created_by=teacher.id)
        register_and_login(client, "filteruser", "student")
        response = client.get("/student/practice", params={"subject": "数学"}, follow_redirects=True)
        assert response.status_code == 200
        assert "question-card" in response.text

    def test_practice_with_semester_filter(self, client, db_session):
        teacher = create_test_user(db_session, "teacher5", "teacher")
        create_test_question(db_session, subject="数学", semester="八年级上册", created_by=teacher.id)
        register_and_login(client, "semuser", "student")
        response = client.get("/student/practice", params={"subject": "数学", "semester": "八年级上册"}, follow_redirects=True)
        assert response.status_code == 200
        assert "question-card" in response.text


class TestTeacherCreateFlow:
    def test_create_question_redirects_to_questions(self, client, db_session):
        register_and_login(client, "createteacher", "teacher")
        csrf = get_csrf_token(client)
        response = client.post("/teacher/questions/create", data={
            "subject": "数学",
            "semester": "八年级上册",
            "chapter": "代数",
            "q_type": "choice",
            "difficulty": "2",
            "content": "2+2=?",
            "option_a": "3",
            "option_b": "4",
            "option_c": "5",
            "option_d": "6",
            "answer": "B",
            "explanation": "2+2=4",
            "_csrf_token": csrf,
        })
        assert response.status_code == 303
        assert "/teacher/questions" in response.headers["location"]

    def test_create_question_page_has_continue_button(self, client, db_session):
        register_and_login(client, "contteacher", "teacher")
        response = client.get("/teacher/questions/create", follow_redirects=True)
        assert response.status_code == 200
        assert "继续出题" in response.text or "再出一题" in response.text

    def test_create_and_continue_redirects_to_create(self, client, db_session):
        register_and_login(client, "redirectteacher", "teacher")
        csrf = get_csrf_token(client)
        response = client.post("/teacher/questions/create", data={
            "subject": "数学",
            "q_type": "choice",
            "difficulty": "1",
            "content": "4+4=?",
            "option_a": "7",
            "option_b": "8",
            "option_c": "9",
            "option_d": "10",
            "answer": "B",
            "continue_creating": "1",
            "_csrf_token": csrf,
        })
        assert response.status_code == 303
        assert "/teacher/questions/create" in response.headers["location"]

    def test_create_and_continue_adds_question(self, client, db_session):
        teacher = create_test_user(db_session, "addteacher", "teacher")
        register_and_login(client, "addteacher", "teacher")
        csrf = get_csrf_token(client)
        client.post("/teacher/questions/create", data={
            "subject": "数学",
            "q_type": "choice",
            "difficulty": "1",
            "content": "3+3=?",
            "option_a": "5",
            "option_b": "6",
            "option_c": "7",
            "option_d": "8",
            "answer": "B",
            "continue_creating": "1",
            "_csrf_token": csrf,
        })
        count = db_session.query(Question).filter(Question.created_by == teacher.id).count()
        assert count == 1


class TestImportFlow:
    def test_import_shows_success_count(self, client, db_session):
        register_and_login(client, "importteacher", "teacher")
        questions = [
            {"subject": "数学", "content": "1+1=?", "answer": "2", "q_type": "fill"},
            {"subject": "英语", "content": "apple=?", "answer": "苹果", "q_type": "fill"},
        ]
        csrf = get_csrf_token(client)
        response = client.post("/teacher/questions/import", files={
            "file": ("test.json", json.dumps(questions).encode(), "application/json"),
        }, data={
            "_csrf_token": csrf,
        })
        assert response.status_code == 200
        assert "成功导入" in response.text
        assert "2" in response.text

    def test_import_rejects_wrong_format(self, client, db_session):
        register_and_login(client, "formatteacher", "teacher")
        csrf = get_csrf_token(client)
        response = client.post("/teacher/questions/import", files={
            "file": ("test.txt", b"hello", "text/plain"),
        }, data={
            "_csrf_token": csrf,
        })
        assert response.status_code == 200
        assert "仅支持" in response.text or "格式" in response.text


import json
