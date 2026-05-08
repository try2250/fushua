from tests.conftest import create_test_user, create_test_question, register_and_login
from app.models import Question, Record


class TestAdaptiveDifficulty:
    def test_adaptive_mode_exists_in_practice_page(self, client, db_session):
        teacher = create_test_user(db_session, "adaptteacher0", "teacher")
        create_test_question(db_session, created_by=teacher.id)
        register_and_login(client, "adaptstudent0", "student")
        response = client.get("/student/practice", follow_redirects=True)
        assert response.status_code == 200
        assert "adaptive" in response.text.lower() or "自适应" in response.text

    def test_adaptive_recommends_easier_after_wrong_answers(self, client, db_session):
        teacher = create_test_user(db_session, "adaptteacher", "teacher")
        q1 = create_test_question(db_session, content="简单题", difficulty=1, created_by=teacher.id)
        q2 = create_test_question(db_session, content="中等题", difficulty=2, created_by=teacher.id)
        q3 = create_test_question(db_session, content="难题", difficulty=3, created_by=teacher.id)
        student = create_test_user(db_session, "adaptstudent", "student")
        for _ in range(3):
            db_session.add(Record(user_id=student.id, question_id=q3.id, user_answer="X", is_correct=False))
        db_session.commit()
        register_and_login(client, "adaptstudent", "student")
        response = client.get("/student/practice?mode=adaptive", follow_redirects=True)
        assert response.status_code == 200
        assert "简单题" in response.text or "中等题" in response.text

    def test_adaptive_recommends_harder_after_correct_answers(self, client, db_session):
        teacher = create_test_user(db_session, "adaptteacher2", "teacher")
        q1 = create_test_question(db_session, content="简单题2", difficulty=1, created_by=teacher.id)
        q2 = create_test_question(db_session, content="中等题2", difficulty=2, created_by=teacher.id)
        q3 = create_test_question(db_session, content="难题2", difficulty=3, created_by=teacher.id)
        student = create_test_user(db_session, "adaptstudent2", "student")
        for _ in range(5):
            db_session.add(Record(user_id=student.id, question_id=q1.id, user_answer="B", is_correct=True))
        db_session.commit()
        register_and_login(client, "adaptstudent2", "student")
        response = client.get("/student/practice?mode=adaptive", follow_redirects=True)
        assert response.status_code == 200
        assert "中等题2" in response.text or "难题2" in response.text
