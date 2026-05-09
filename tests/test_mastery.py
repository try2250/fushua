from tests.conftest import create_test_user, create_test_question, register_and_login, get_csrf_token
from app.models import MasteryRecord, Record


class TestMasteryRecord:
    def test_wrong_answer_creates_unmastered(self, client, db_session):
        teacher = create_test_user(db_session, "mteacher1", "teacher")
        q = create_test_question(db_session, created_by=teacher.id)
        register_and_login(client, "mstudent1", "student")
        csrf = get_csrf_token(client)
        response = client.post("/student/practice/submit", data={
            f"answer_{q.id}": "A",
            "_csrf_token": csrf,
        }, follow_redirects=True)
        assert response.status_code == 200
        mr = db_session.query(MasteryRecord).filter(
            MasteryRecord.question_id == q.id,
        ).first()
        assert mr is not None
        assert mr.status == "unmastered"
        assert mr.consecutive_correct == 0

    def test_correct_answer_sets_reviewing(self, client, db_session):
        teacher = create_test_user(db_session, "mteacher2", "teacher")
        q = create_test_question(db_session, created_by=teacher.id)
        register_and_login(client, "mstudent2", "student")
        csrf = get_csrf_token(client)
        client.post("/student/practice/submit", data={
            f"answer_{q.id}": "B",
            "_csrf_token": csrf,
        }, follow_redirects=True)
        mr = db_session.query(MasteryRecord).filter(
            MasteryRecord.question_id == q.id,
        ).first()
        assert mr is not None
        assert mr.status == "reviewing"
        assert mr.consecutive_correct == 1

    def test_three_correct_sets_mastered(self, client, db_session):
        teacher = create_test_user(db_session, "mteacher3", "teacher")
        q = create_test_question(db_session, created_by=teacher.id)
        register_and_login(client, "mstudent3", "student")
        csrf = get_csrf_token(client)
        for _ in range(3):
            client.post("/student/practice/submit", data={
                f"answer_{q.id}": "B",
                "_csrf_token": csrf,
            }, follow_redirects=True)
        mr = db_session.query(MasteryRecord).filter(
            MasteryRecord.question_id == q.id,
        ).first()
        assert mr.status == "mastered"
        assert mr.consecutive_correct == 3

    def test_wrong_resets_to_unmastered(self, client, db_session):
        teacher = create_test_user(db_session, "mteacher4", "teacher")
        q = create_test_question(db_session, created_by=teacher.id)
        register_and_login(client, "mstudent4", "student")
        csrf = get_csrf_token(client)
        client.post("/student/practice/submit", data={
            f"answer_{q.id}": "B",
            "_csrf_token": csrf,
        }, follow_redirects=True)
        mr = db_session.query(MasteryRecord).filter(
            MasteryRecord.question_id == q.id,
        ).first()
        assert mr.status == "reviewing"
        assert mr.consecutive_correct == 1
        client.post("/student/practice/submit", data={
            f"answer_{q.id}": "A",
            "_csrf_token": csrf,
        }, follow_redirects=True)
        db_session.refresh(mr)
        assert mr.status == "unmastered"
        assert mr.consecutive_correct == 0

    def test_wrong_after_mastered_resets(self, client, db_session):
        teacher = create_test_user(db_session, "mteacher5", "teacher")
        q = create_test_question(db_session, created_by=teacher.id)
        register_and_login(client, "mstudent5", "student")
        csrf = get_csrf_token(client)
        for _ in range(3):
            client.post("/student/practice/submit", data={
                f"answer_{q.id}": "B",
                "_csrf_token": csrf,
            }, follow_redirects=True)
        mr = db_session.query(MasteryRecord).filter(
            MasteryRecord.question_id == q.id,
        ).first()
        assert mr.status == "mastered"
        client.post("/student/practice/submit", data={
            f"answer_{q.id}": "A",
            "_csrf_token": csrf,
        }, follow_redirects=True)
        db_session.refresh(mr)
        assert mr.status == "unmastered"
        assert mr.consecutive_correct == 0

    def test_unique_constraint(self, client, db_session):
        teacher = create_test_user(db_session, "mteacher6", "teacher")
        q = create_test_question(db_session, created_by=teacher.id)
        register_and_login(client, "mstudent6", "student")
        csrf = get_csrf_token(client)
        client.post("/student/practice/submit", data={
            f"answer_{q.id}": "B",
            "_csrf_token": csrf,
        }, follow_redirects=True)
        client.post("/student/practice/submit", data={
            f"answer_{q.id}": "B",
            "_csrf_token": csrf,
        }, follow_redirects=True)
        count = db_session.query(MasteryRecord).filter(
            MasteryRecord.question_id == q.id,
        ).count()
        assert count == 1

    def test_mistakes_page_shows_mastery_status(self, client, db_session):
        teacher = create_test_user(db_session, "mteacher7", "teacher")
        q = create_test_question(db_session, content="掌握状态题", created_by=teacher.id)
        register_and_login(client, "mstudent7", "student")
        csrf = get_csrf_token(client)
        client.post("/student/practice/submit", data={
            f"answer_{q.id}": "A",
            "_csrf_token": csrf,
        }, follow_redirects=True)
        response = client.get("/student/mistakes", follow_redirects=True)
        assert response.status_code == 200
        assert "未掌握" in response.text

    def test_mistakes_page_filter_by_status(self, client, db_session):
        teacher = create_test_user(db_session, "mteacher8", "teacher")
        q = create_test_question(db_session, content="筛选测试题", created_by=teacher.id)
        register_and_login(client, "mstudent8", "student")
        csrf = get_csrf_token(client)
        client.post("/student/practice/submit", data={
            f"answer_{q.id}": "A",
            "_csrf_token": csrf,
        }, follow_redirects=True)
        response = client.get("/student/mistakes?status=unmastered", follow_redirects=True)
        assert response.status_code == 200
        assert "筛选测试题" in response.text
        response = client.get("/student/mistakes?status=mastered", follow_redirects=True)
        assert response.status_code == 200
        assert "筛选测试题" not in response.text

    def test_mistakes_page_shows_reviewing(self, client, db_session):
        teacher = create_test_user(db_session, "mteacher9", "teacher")
        q = create_test_question(db_session, content="复习中测试题", created_by=teacher.id)
        user = create_test_user(db_session, "mstudent9", "student")
        mr = MasteryRecord(user_id=user.id, question_id=q.id, status="reviewing", consecutive_correct=1)
        db_session.add(mr)
        record = Record(user_id=user.id, question_id=q.id, user_answer="A", is_correct=False)
        db_session.add(record)
        db_session.commit()
        register_and_login(client, "mstudent9", "student")
        response = client.get("/student/mistakes", follow_redirects=True)
        assert response.status_code == 200
        assert "复习中" in response.text

    def test_mistakes_page_status_counts(self, client, db_session):
        teacher = create_test_user(db_session, "mteacher10", "teacher")
        q1 = create_test_question(db_session, content="计数题1", created_by=teacher.id)
        q2 = create_test_question(db_session, content="计数题2", created_by=teacher.id)
        user = create_test_user(db_session, "mstudent10", "student")
        mr1 = MasteryRecord(user_id=user.id, question_id=q1.id, status="unmastered", consecutive_correct=0)
        mr2 = MasteryRecord(user_id=user.id, question_id=q2.id, status="reviewing", consecutive_correct=2)
        db_session.add_all([mr1, mr2])
        db_session.add(Record(user_id=user.id, question_id=q1.id, user_answer="A", is_correct=False))
        db_session.add(Record(user_id=user.id, question_id=q2.id, user_answer="A", is_correct=False))
        db_session.commit()
        register_and_login(client, "mstudent10", "student")
        response = client.get("/student/mistakes", follow_redirects=True)
        assert response.status_code == 200
        assert "未掌握 (1)" in response.text
        assert "复习中 (1)" in response.text

    def test_two_correct_then_wrong_resets(self, client, db_session):
        teacher = create_test_user(db_session, "mteacher11", "teacher")
        q = create_test_question(db_session, created_by=teacher.id)
        register_and_login(client, "mstudent11", "student")
        csrf = get_csrf_token(client)
        client.post("/student/practice/submit", data={
            f"answer_{q.id}": "B",
            "_csrf_token": csrf,
        }, follow_redirects=True)
        client.post("/student/practice/submit", data={
            f"answer_{q.id}": "B",
            "_csrf_token": csrf,
        }, follow_redirects=True)
        mr = db_session.query(MasteryRecord).filter(
            MasteryRecord.question_id == q.id,
        ).first()
        assert mr.status == "reviewing"
        assert mr.consecutive_correct == 2
        client.post("/student/practice/submit", data={
            f"answer_{q.id}": "A",
            "_csrf_token": csrf,
        }, follow_redirects=True)
        db_session.refresh(mr)
        assert mr.status == "unmastered"
        assert mr.consecutive_correct == 0
