import pytest
from datetime import date, timedelta
from tests.conftest import create_test_user, create_test_question, register_and_login
from app.models import Record, WeeklyScore, ClassGroup, ClassMember


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


# ─── Plan 2.1 WeeklyScore model tests (TDD Task 3) ───

def test_weekly_score_creation(db):
    ws = WeeklyScore(user_id=1, class_id=1, week_start=date.today(), score=12)
    db.add(ws); db.commit(); db.refresh(ws)
    assert ws.score == 12
    assert ws.week_start == date.today()


def test_weekly_score_unique_constraint(db, teacher_a):
    ws1 = WeeklyScore(user_id=teacher_a.id, class_id=1, week_start=date.today(), score=5)
    db.add(ws1); db.commit()
    ws2 = WeeklyScore(user_id=teacher_a.id, class_id=1, week_start=date.today(), score=10)
    db.add(ws2)
    with pytest.raises(Exception):
        db.commit()


# ─── Plan 2.1 leaderboard_service tests (TDD Task 5) ───
from app.services.leaderboard_service import leaderboard_service
from app.core.security import get_week_start


def test_update_weekly_score_creates(db):
    monday = date.today() - timedelta(days=date.today().weekday())
    leaderboard_service.update_weekly_score(db, user_id=1, class_id=10, week_start=monday, is_correct=True)
    ws = db.query(WeeklyScore).filter(WeeklyScore.user_id == 1, WeeklyScore.class_id == 10).first()
    assert ws is not None
    assert ws.score == 1


def test_update_correct_adds_score(db):
    monday = date.today() - timedelta(days=date.today().weekday())
    db.add(WeeklyScore(user_id=1, class_id=11, week_start=monday, score=3))
    db.commit()
    leaderboard_service.update_weekly_score(db, user_id=1, class_id=11, week_start=monday, is_correct=True)
    ws = db.query(WeeklyScore).filter(WeeklyScore.user_id == 1, WeeklyScore.class_id == 11).first()
    assert ws.score == 4


def test_wrong_answer_does_not_add_score(db):
    monday = date.today() - timedelta(days=date.today().weekday())
    leaderboard_service.update_weekly_score(db, user_id=1, class_id=12, week_start=monday, is_correct=False)
    ws = db.query(WeeklyScore).filter(WeeklyScore.user_id == 1, WeeklyScore.class_id == 12).first()
    assert ws is None  # no score entry for wrong answers


def test_get_leaderboard_returns_top_students(db, teacher_a):
    monday = date.today() - timedelta(days=date.today().weekday())
    cls = ClassGroup(name="排行班", created_by=teacher_a.id)
    db.add(cls); db.commit(); db.refresh(cls)
    for uid in range(10):
        db.add(WeeklyScore(user_id=uid+1, class_id=cls.id, week_start=monday, score=uid+1))
    db.commit()
    board = leaderboard_service.get_class_leaderboard(db, cls.id, monday)
    assert len(board) <= 10
    assert board[0]["score"] >= board[-1]["score"]  # descending
