from tests.conftest import create_test_user, register_and_login, get_csrf_token, create_test_question
from app.models import Record, Assignment, AssignmentRecord, StudyPlan


class TestDashboard:
    def test_dashboard_requires_login(self, client, db_session):
        response = client.get("/student/dashboard", follow_redirects=False)
        assert response.status_code == 303
        assert "/login" in response.headers.get("location", "")

    def test_dashboard_accessible_after_login(self, client, db_session):
        register_and_login(client, "dashuser", "student")
        response = client.get("/student/dashboard", follow_redirects=True)
        assert response.status_code == 200
        assert "今日学习" in response.text

    def test_dashboard_shows_pending_assignments(self, client, db_session):
        user = create_test_user(db_session, "dashassign", "student")
        assignment = Assignment(
            title="数学作业",
            description="完成第三章",
            question_ids="1,2,3",
            created_by=user.id,
        )
        db_session.add(assignment)
        db_session.commit()
        register_and_login(client, "dashassign", "student")
        response = client.get("/student/dashboard", follow_redirects=True)
        assert response.status_code == 200
        assert "数学作业" in response.text
        assert "待完成作业" in response.text

    def test_dashboard_hides_completed_assignments(self, client, db_session):
        user = create_test_user(db_session, "dashcomp", "student")
        assignment = Assignment(
            title="已完成作业",
            description="",
            question_ids="1",
            created_by=user.id,
        )
        db_session.add(assignment)
        db_session.commit()
        ar = AssignmentRecord(
            assignment_id=assignment.id,
            user_id=user.id,
            completed=True,
        )
        db_session.add(ar)
        db_session.commit()
        register_and_login(client, "dashcomp", "student")
        response = client.get("/student/dashboard", follow_redirects=True)
        assert response.status_code == 200
        assert "已完成作业" not in response.text

    def test_dashboard_shows_unmastered_mistakes(self, client, db_session):
        user = create_test_user(db_session, "dashmistake", "student")
        q = create_test_question(db_session, subject="数学", created_by=user.id)
        record = Record(user_id=user.id, question_id=q.id, user_answer="A", is_correct=False)
        db_session.add(record)
        db_session.commit()
        register_and_login(client, "dashmistake", "student")
        response = client.get("/student/dashboard", follow_redirects=True)
        assert response.status_code == 200
        assert "错题待复习" in response.text

    def test_dashboard_shows_today_progress(self, client, db_session):
        user = create_test_user(db_session, "dashprog", "student")
        q = create_test_question(db_session, subject="英语", created_by=user.id)
        record = Record(user_id=user.id, question_id=q.id, user_answer="A", is_correct=True)
        db_session.add(record)
        db_session.commit()
        register_and_login(client, "dashprog", "student")
        response = client.get("/student/dashboard", follow_redirects=True)
        assert response.status_code == 200
        assert "今日进度" in response.text

    def test_dashboard_shows_daily_goal_from_plan(self, client, db_session):
        user = create_test_user(db_session, "dashplan", "student")
        plan = StudyPlan(user_id=user.id, subject="数学", daily_goal=20, active=True)
        db_session.add(plan)
        db_session.commit()
        register_and_login(client, "dashplan", "student")
        response = client.get("/student/dashboard", follow_redirects=True)
        assert response.status_code == 200
        assert "20" in response.text

    def test_dashboard_shows_recommended_practice(self, client, db_session):
        user = create_test_user(db_session, "dashrec", "student")
        q = create_test_question(db_session, subject="物理", created_by=user.id)
        record = Record(user_id=user.id, question_id=q.id, user_answer="A", is_correct=False)
        db_session.add(record)
        db_session.commit()
        register_and_login(client, "dashrec", "student")
        response = client.get("/student/dashboard", follow_redirects=True)
        assert response.status_code == 200
        assert "推荐练习" in response.text

    def test_index_redirects_student_to_dashboard(self, client, db_session):
        register_and_login(client, "dashredirect", "student")
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 303
        assert "/student/dashboard" in response.headers.get("location", "")

    def test_index_redirects_teacher_to_questions(self, client, db_session):
        register_and_login(client, "dashteacher", "teacher")
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 303
        assert "/teacher/questions" in response.headers.get("location", "")

    def test_index_no_redirect_for_anonymous(self, client, db_session):
        response = client.get("/", follow_redirects=True)
        assert response.status_code == 200
        assert "立即注册" in response.text

    def test_dashboard_progress_zero_without_records(self, client, db_session):
        register_and_login(client, "dashempty", "student")
        response = client.get("/student/dashboard", follow_redirects=True)
        assert response.status_code == 200
        assert "0" in response.text
