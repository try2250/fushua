from datetime import datetime, timedelta
from tests.conftest import create_test_user, register_and_login, create_test_question
from app.models import Record, StudyPlan


class TestAchievement:
    def test_profile_shows_streak(self, client, db_session):
        user = create_test_user(db_session, "achstreak", "student")
        q = create_test_question(db_session, subject="数学", created_by=user.id)
        record = Record(user_id=user.id, question_id=q.id, user_answer="B", is_correct=True)
        db_session.add(record)
        db_session.commit()
        register_and_login(client, "achstreak", "student")
        response = client.get("/student/profile", follow_redirects=True)
        assert response.status_code == 200
        assert "连续学习天数" in response.text

    def test_profile_shows_today_goal_pct(self, client, db_session):
        user = create_test_user(db_session, "achgoal", "student")
        q = create_test_question(db_session, subject="英语", created_by=user.id)
        record = Record(user_id=user.id, question_id=q.id, user_answer="B", is_correct=True)
        db_session.add(record)
        db_session.commit()
        register_and_login(client, "achgoal", "student")
        response = client.get("/student/profile", follow_redirects=True)
        assert response.status_code == 200
        assert "今日目标" in response.text

    def test_profile_today_goal_with_plan(self, client, db_session):
        user = create_test_user(db_session, "achplan", "student")
        q = create_test_question(db_session, subject="数学", created_by=user.id)
        record = Record(user_id=user.id, question_id=q.id, user_answer="B", is_correct=True)
        db_session.add(record)
        plan = StudyPlan(user_id=user.id, subject="数学", daily_goal=5, active=True)
        db_session.add(plan)
        db_session.commit()
        register_and_login(client, "achplan", "student")
        response = client.get("/student/profile", follow_redirects=True)
        assert response.status_code == 200
        assert "20.0%" in response.text

    def test_profile_shows_accuracy_change_up(self, client, db_session):
        user = create_test_user(db_session, "achaccup", "student")
        q1 = create_test_question(db_session, subject="数学", content="q1", created_by=user.id)
        q2 = create_test_question(db_session, subject="数学", content="q2", created_by=user.id)
        q3 = create_test_question(db_session, subject="数学", content="q3", created_by=user.id)
        q4 = create_test_question(db_session, subject="数学", content="q4", created_by=user.id)
        now = datetime.now()
        prev_time = now - timedelta(days=10)
        recent_time = now - timedelta(days=3)
        db_session.add(Record(user_id=user.id, question_id=q1.id, user_answer="A", is_correct=False, created_at=prev_time))
        db_session.add(Record(user_id=user.id, question_id=q2.id, user_answer="B", is_correct=False, created_at=prev_time))
        db_session.add(Record(user_id=user.id, question_id=q3.id, user_answer="B", is_correct=True, created_at=recent_time))
        db_session.add(Record(user_id=user.id, question_id=q4.id, user_answer="B", is_correct=True, created_at=recent_time))
        db_session.commit()
        register_and_login(client, "achaccup", "student")
        response = client.get("/student/profile", follow_redirects=True)
        assert response.status_code == 200
        assert "accuracy-up" in response.text

    def test_profile_shows_accuracy_change_down(self, client, db_session):
        user = create_test_user(db_session, "achaccdn", "student")
        q1 = create_test_question(db_session, subject="数学", content="q1", created_by=user.id)
        q2 = create_test_question(db_session, subject="数学", content="q2", created_by=user.id)
        q3 = create_test_question(db_session, subject="数学", content="q3", created_by=user.id)
        q4 = create_test_question(db_session, subject="数学", content="q4", created_by=user.id)
        now = datetime.now()
        prev_time = now - timedelta(days=10)
        recent_time = now - timedelta(days=3)
        db_session.add(Record(user_id=user.id, question_id=q1.id, user_answer="B", is_correct=True, created_at=prev_time))
        db_session.add(Record(user_id=user.id, question_id=q2.id, user_answer="B", is_correct=True, created_at=prev_time))
        db_session.add(Record(user_id=user.id, question_id=q3.id, user_answer="A", is_correct=False, created_at=recent_time))
        db_session.add(Record(user_id=user.id, question_id=q4.id, user_answer="A", is_correct=False, created_at=recent_time))
        db_session.commit()
        register_and_login(client, "achaccdn", "student")
        response = client.get("/student/profile", follow_redirects=True)
        assert response.status_code == 200
        assert "accuracy-down" in response.text

    def test_profile_shows_chapter_badge(self, client, db_session):
        user = create_test_user(db_session, "achbadge", "student")
        q1 = create_test_question(db_session, subject="数学", chapter="代数", content="q1", created_by=user.id)
        q2 = create_test_question(db_session, subject="数学", chapter="代数", content="q2", created_by=user.id)
        q3 = create_test_question(db_session, subject="数学", chapter="代数", content="q3", created_by=user.id)
        q4 = create_test_question(db_session, subject="数学", chapter="代数", content="q4", created_by=user.id)
        q5 = create_test_question(db_session, subject="数学", chapter="代数", content="q5", created_by=user.id)
        q6 = create_test_question(db_session, subject="数学", chapter="代数", content="q6", created_by=user.id)
        db_session.add(Record(user_id=user.id, question_id=q1.id, user_answer="B", is_correct=True))
        db_session.add(Record(user_id=user.id, question_id=q2.id, user_answer="B", is_correct=True))
        db_session.add(Record(user_id=user.id, question_id=q3.id, user_answer="B", is_correct=True))
        db_session.add(Record(user_id=user.id, question_id=q4.id, user_answer="B", is_correct=True))
        db_session.add(Record(user_id=user.id, question_id=q5.id, user_answer="B", is_correct=True))
        db_session.add(Record(user_id=user.id, question_id=q6.id, user_answer="A", is_correct=False))
        db_session.commit()
        register_and_login(client, "achbadge", "student")
        response = client.get("/student/profile", follow_redirects=True)
        assert response.status_code == 200
        assert "章节徽章" in response.text
        assert "代数" in response.text

    def test_profile_no_badge_below_80(self, client, db_session):
        user = create_test_user(db_session, "achnobadge", "student")
        q1 = create_test_question(db_session, subject="数学", chapter="几何", content="q1", created_by=user.id)
        q2 = create_test_question(db_session, subject="数学", chapter="几何", content="q2", created_by=user.id)
        q3 = create_test_question(db_session, subject="数学", chapter="几何", content="q3", created_by=user.id)
        db_session.add(Record(user_id=user.id, question_id=q1.id, user_answer="A", is_correct=False))
        db_session.add(Record(user_id=user.id, question_id=q2.id, user_answer="A", is_correct=False))
        db_session.add(Record(user_id=user.id, question_id=q3.id, user_answer="B", is_correct=True))
        db_session.commit()
        register_and_login(client, "achnobadge", "student")
        response = client.get("/student/profile", follow_redirects=True)
        assert response.status_code == 200
        assert "章节徽章" not in response.text

    def test_profile_achievement_section_no_records(self, client, db_session):
        register_and_login(client, "achempty", "student")
        response = client.get("/student/profile", follow_redirects=True)
        assert response.status_code == 200
        assert "学习成就" in response.text
        assert "0%" in response.text

    def test_profile_accuracy_change_flat(self, client, db_session):
        user = create_test_user(db_session, "achflat", "student")
        q1 = create_test_question(db_session, subject="数学", content="q1", created_by=user.id)
        now = datetime.now()
        recent_time = now - timedelta(days=3)
        db_session.add(Record(user_id=user.id, question_id=q1.id, user_answer="B", is_correct=True, created_at=recent_time))
        db_session.commit()
        register_and_login(client, "achflat", "student")
        response = client.get("/student/profile", follow_redirects=True)
        assert response.status_code == 200
        assert "accuracy-flat" in response.text or "accuracy-up" in response.text
