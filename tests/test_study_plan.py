from tests.conftest import create_test_user, register_and_login, get_csrf_token
from app.models import StudyPlan


class TestStudyPlan:
    def test_create_study_plan(self, client, db_session):
        register_and_login(client, "planuser", "student")
        csrf = get_csrf_token(client)
        response = client.post("/student/plans/create", data={
            "subject": "数学", "daily_goal": "20", "semester": "八年级上册",
            "_csrf_token": csrf,
        })
        assert response.status_code == 303
        plan = db_session.query(StudyPlan).first()
        assert plan is not None
        assert plan.daily_goal == 20

    def test_plans_page_shows_plans(self, client, db_session):
        register_and_login(client, "planuser2", "student")
        csrf = get_csrf_token(client)
        client.post("/student/plans/create", data={
            "subject": "英语", "daily_goal": "15", "_csrf_token": csrf,
        })
        response = client.get("/student/plans", follow_redirects=True)
        assert response.status_code == 200
        assert "英语" in response.text

    def test_delete_plan(self, client, db_session):
        user = create_test_user(db_session, "planuser3", "student")
        plan = StudyPlan(user_id=user.id, subject="物理", daily_goal=10)
        db_session.add(plan)
        db_session.commit()
        register_and_login(client, "planuser3", "student")
        csrf = get_csrf_token(client)
        response = client.post(f"/student/plans/{plan.id}/delete", data={"_csrf_token": csrf})
        assert response.status_code == 303
        count = db_session.query(StudyPlan).count()
        assert count == 0
