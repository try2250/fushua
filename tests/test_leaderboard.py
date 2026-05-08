from tests.conftest import create_test_user, create_test_question, register_and_login
from app.models import Record


class TestLeaderboard:
    def test_leaderboard_page_accessible(self, client, db_session):
        register_and_login(client, "leaduser", "student")
        response = client.get("/leaderboard", follow_redirects=True)
        assert response.status_code == 200
        assert "排行榜" in response.text

    def test_leaderboard_shows_rankings(self, client, db_session):
        user = create_test_user(db_session, "leaduser2", "student")
        question = create_test_question(db_session, created_by=user.id)
        record = Record(user_id=user.id, question_id=question.id, user_answer="B", is_correct=True)
        db_session.add(record)
        db_session.commit()
        register_and_login(client, "leaduser2", "student")
        response = client.get("/leaderboard", follow_redirects=True)
        assert response.status_code == 200
        assert "排名" in response.text or "rank" in response.text.lower()
