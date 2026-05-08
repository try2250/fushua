from tests.conftest import create_test_user, register_and_login, get_csrf_token
from app.models import Question


class TestQuestionImage:
    def test_question_has_image_url_field(self, client, db_session):
        teacher = create_test_user(db_session, "imgteacher", "teacher")
        q = Question(
            subject="数学", content="看图答题", answer="A",
            image_url="/uploads/test.png", created_by=teacher.id,
        )
        db_session.add(q)
        db_session.commit()
        assert q.image_url == "/uploads/test.png"

    def test_create_question_with_image_url(self, client, db_session):
        register_and_login(client, "imgteacher2", "teacher")
        csrf = get_csrf_token(client)
        response = client.post("/teacher/questions/create", data={
            "subject": "数学", "q_type": "choice", "difficulty": "2",
            "content": "看图选答案", "option_a": "A", "option_b": "B",
            "option_c": "C", "option_d": "D", "answer": "A",
            "image_url": "/uploads/geometry.png",
            "_csrf_token": csrf,
        })
        assert response.status_code == 303
        q = db_session.query(Question).first()
        assert q is not None
        assert q.image_url == "/uploads/geometry.png"

    def test_practice_page_shows_image(self, client, db_session):
        teacher = create_test_user(db_session, "imgteacher3", "teacher")
        q = Question(
            subject="数学", content="看图题", answer="A",
            image_url="/uploads/geo.png", created_by=teacher.id,
            q_type="choice", difficulty=2,
            option_a="A", option_b="B", option_c="C", option_d="D",
        )
        db_session.add(q)
        db_session.commit()
        register_and_login(client, "imgstudent", "student")
        response = client.get("/student/practice", follow_redirects=True)
        assert response.status_code == 200
        assert "question-image" in response.text
        assert "/uploads/geo.png" in response.text
