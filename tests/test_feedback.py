from tests.conftest import create_test_user, register_and_login, get_csrf_token
from app.models import Feedback


class TestFeedbackModel:
    def test_feedback_model_exists(self, db_session):
        fb = Feedback(content="测试反馈", role="student", page_path="/student/dashboard")
        db_session.add(fb)
        db_session.commit()
        assert fb.id is not None
        assert fb.content == "测试反馈"
        assert fb.role == "student"
        assert fb.page_path == "/student/dashboard"
        assert fb.created_at is not None

    def test_feedback_nullable_user_id(self, db_session):
        fb = Feedback(content="匿名反馈", user_id=None, role="", page_path="/")
        db_session.add(fb)
        db_session.commit()
        assert fb.id is not None
        assert fb.user_id is None


class TestFeedbackRoute:
    def test_submit_feedback_logged_in(self, client, db_session):
        user = create_test_user(db_session, "fbuser", "student")
        register_and_login(client, "fbuser", "student")
        csrf = get_csrf_token(client)
        response = client.post("/feedback", data={
            "_csrf_token": csrf,
            "content": "页面加载太慢了",
            "page_path": "/student/dashboard",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        fb = db_session.query(Feedback).first()
        assert fb is not None
        assert fb.content == "页面加载太慢了"
        assert fb.page_path == "/student/dashboard"
        assert fb.role == "student"
        assert fb.user_id == user.id

    def test_submit_feedback_anonymous(self, client, db_session):
        csrf = get_csrf_token(client)
        response = client.post("/feedback", data={
            "_csrf_token": csrf,
            "content": "匿名反馈内容",
            "page_path": "/browse",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        fb = db_session.query(Feedback).first()
        assert fb is not None
        assert fb.content == "匿名反馈内容"
        assert fb.user_id is None
        assert fb.role == ""

    def test_submit_feedback_empty_content(self, client, db_session):
        csrf = get_csrf_token(client)
        response = client.post("/feedback", data={
            "_csrf_token": csrf,
            "content": "",
            "page_path": "/",
        })
        assert response.status_code == 400
        data = response.json()
        assert data["ok"] is False

    def test_submit_feedback_csrf_required(self, client, db_session):
        response = client.post("/feedback", data={
            "content": "没有CSRF",
            "page_path": "/",
        })
        assert response.status_code == 403

    def test_submit_feedback_teacher_role(self, client, db_session):
        register_and_login(client, "fbteacher", "teacher")
        csrf = get_csrf_token(client)
        response = client.post("/feedback", data={
            "_csrf_token": csrf,
            "content": "教师反馈",
            "page_path": "/teacher/questions",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        fb = db_session.query(Feedback).first()
        assert fb.role == "teacher"


class TestFeedbackUI:
    def test_feedback_button_in_page(self, client, db_session):
        response = client.get("/", follow_redirects=True)
        assert response.status_code == 200
        assert "反馈问题" in response.text
        assert "feedback-form" in response.text

    def test_feedback_widget_in_logged_in_page(self, client, db_session):
        register_and_login(client, "fbuiuser", "student")
        response = client.get("/student/dashboard", follow_redirects=True)
        assert response.status_code == 200
        assert "反馈问题" in response.text
        assert "feedback-page-path" in response.text
