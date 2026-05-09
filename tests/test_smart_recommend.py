from tests.conftest import create_test_user, create_test_question, register_and_login
from app.models import MasteryRecord, Record, Question
from app.routers.student import _smart_select
from tests.conftest import TestingSessionLocal


class TestSmartRecommendWeights:
    def test_returns_tuples_with_reasons(self, client, db_session):
        teacher = create_test_user(db_session, "srteacher1", "teacher")
        for i in range(10):
            create_test_question(db_session, content=f"题目{i}", created_by=teacher.id)
        user = create_test_user(db_session, "srstudent1", "student")
        db = TestingSessionLocal()
        try:
            result = _smart_select(user.id, db, count=5)
            assert len(result) <= 5
            for item in result:
                assert isinstance(item, tuple)
                assert len(item) == 2
                assert isinstance(item[0], Question)
                assert item[1] in ("错题复习", "薄弱章节", "难度适配", "随机补充")
        finally:
            db.close()

    def test_unmastered_weight_40_percent(self, client, db_session):
        teacher = create_test_user(db_session, "srteacher2", "teacher")
        questions = []
        for i in range(20):
            q = create_test_question(db_session, content=f"题{i}", chapter="代数", created_by=teacher.id)
            questions.append(q)
        user = create_test_user(db_session, "srstudent2", "student")
        for q in questions[:10]:
            mr = MasteryRecord(user_id=user.id, question_id=q.id, status="unmastered", consecutive_correct=0)
            db_session.add(mr)
        db_session.commit()
        db = TestingSessionLocal()
        try:
            result = _smart_select(user.id, db, count=10)
            unmastered_count = sum(1 for _, reason in result if reason == "错题复习")
            assert unmastered_count >= 3
        finally:
            db.close()

    def test_weak_chapter_weight_30_percent(self, client, db_session):
        teacher = create_test_user(db_session, "srteacher3", "teacher")
        for i in range(10):
            create_test_question(db_session, content=f"弱章题{i}", chapter="弱章节", created_by=teacher.id)
        for i in range(10):
            create_test_question(db_session, content=f"强章题{i}", chapter="强章节", created_by=teacher.id)
        user = create_test_user(db_session, "srstudent3", "student")
        weak_q = db_session.query(Question).filter(Question.chapter == "弱章节").first()
        strong_q = db_session.query(Question).filter(Question.chapter == "强章节").first()
        for _ in range(5):
            db_session.add(Record(user_id=user.id, question_id=weak_q.id, user_answer="A", is_correct=False))
        for _ in range(5):
            db_session.add(Record(user_id=user.id, question_id=strong_q.id, user_answer="B", is_correct=True))
        db_session.commit()
        db = TestingSessionLocal()
        try:
            result = _smart_select(user.id, db, count=10)
            weak_chapter_count = sum(1 for _, reason in result if reason == "薄弱章节")
            assert weak_chapter_count >= 2
        finally:
            db.close()

    def test_difficulty_adapt_high_accuracy(self, client, db_session):
        teacher = create_test_user(db_session, "srteacher4", "teacher")
        for d in range(1, 6):
            create_test_question(db_session, content=f"难度{d}题", difficulty=d, created_by=teacher.id)
        user = create_test_user(db_session, "srstudent4", "student")
        easy_q = db_session.query(Question).filter(Question.difficulty == 1).first()
        for _ in range(10):
            db_session.add(Record(user_id=user.id, question_id=easy_q.id, user_answer="B", is_correct=True))
        db_session.commit()
        db = TestingSessionLocal()
        try:
            result = _smart_select(user.id, db, count=5)
            difficulty_items = [q for q, reason in result if reason == "难度适配"]
            for q in difficulty_items:
                assert q.difficulty >= 3
        finally:
            db.close()

    def test_difficulty_adapt_low_accuracy(self, client, db_session):
        teacher = create_test_user(db_session, "srteacher5", "teacher")
        for d in range(1, 6):
            create_test_question(db_session, content=f"低准确率难度{d}题", difficulty=d, created_by=teacher.id)
        user = create_test_user(db_session, "srstudent5", "student")
        hard_q = db_session.query(Question).filter(Question.difficulty == 5).first()
        for _ in range(10):
            db_session.add(Record(user_id=user.id, question_id=hard_q.id, user_answer="A", is_correct=False))
        db_session.commit()
        db = TestingSessionLocal()
        try:
            result = _smart_select(user.id, db, count=5)
            difficulty_items = [q for q, reason in result if reason == "难度适配"]
            for q in difficulty_items:
                assert q.difficulty <= 2
        finally:
            db.close()

    def test_no_duplicate_questions(self, client, db_session):
        teacher = create_test_user(db_session, "srteacher6", "teacher")
        for i in range(5):
            create_test_question(db_session, content=f"去重题{i}", chapter="重章", created_by=teacher.id)
        user = create_test_user(db_session, "srstudent6", "student")
        all_qs = db_session.query(Question).filter(Question.content.like("去重题%")).all()
        for q in all_qs:
            mr = MasteryRecord(user_id=user.id, question_id=q.id, status="unmastered", consecutive_correct=0)
            db_session.add(mr)
            db_session.add(Record(user_id=user.id, question_id=q.id, user_answer="A", is_correct=False))
        db_session.commit()
        db = TestingSessionLocal()
        try:
            result = _smart_select(user.id, db, count=5)
            ids = [q.id for q, _ in result]
            assert len(ids) == len(set(ids))
        finally:
            db.close()

    def test_random_fill_when_pools_exhausted(self, client, db_session):
        teacher = create_test_user(db_session, "srteacher7", "teacher")
        for i in range(15):
            create_test_question(db_session, content=f"随机题{i}", created_by=teacher.id)
        user = create_test_user(db_session, "srstudent7", "student")
        db = TestingSessionLocal()
        try:
            result = _smart_select(user.id, db, count=10)
            assert len(result) == 10
        finally:
            db.close()

    def test_empty_question_pool(self, client, db_session):
        user = create_test_user(db_session, "srstudent8", "student")
        db = TestingSessionLocal()
        try:
            result = _smart_select(user.id, db, count=5)
            assert result == []
        finally:
            db.close()

    def test_dashboard_shows_recommend_reasons(self, client, db_session):
        teacher = create_test_user(db_session, "srteacher9", "teacher")
        for i in range(5):
            create_test_question(db_session, content=f"推荐理由题{i}", created_by=teacher.id)
        user = create_test_user(db_session, "srstudent9", "student")
        q = db_session.query(Question).filter(Question.content.like("推荐理由题%")).first()
        mr = MasteryRecord(user_id=user.id, question_id=q.id, status="unmastered", consecutive_correct=0)
        db_session.add(mr)
        db_session.commit()
        register_and_login(client, "srstudent9", "student")
        response = client.get("/student/dashboard", follow_redirects=True)
        assert response.status_code == 200
        assert "错题复习" in response.text or "薄弱章节" in response.text or "难度适配" in response.text or "随机补充" in response.text

    def test_adaptive_mode_returns_tuples(self, client, db_session):
        teacher = create_test_user(db_session, "srteacher10", "teacher")
        for d in range(1, 4):
            create_test_question(db_session, content=f"自适应难度{d}", difficulty=d, created_by=teacher.id)
        user = create_test_user(db_session, "srstudent10", "student")
        db = TestingSessionLocal()
        try:
            result = _smart_select(user.id, db, count=3, mode="adaptive")
            for item in result:
                assert isinstance(item, tuple)
                assert len(item) == 2
                assert item[1] == "难度适配"
        finally:
            db.close()

    def test_practice_page_works_with_new_format(self, client, db_session):
        teacher = create_test_user(db_session, "srteacher11", "teacher")
        for i in range(5):
            create_test_question(db_session, content=f"练习题{i}", created_by=teacher.id)
        register_and_login(client, "srstudent11", "student")
        response = client.get("/student/practice?mode=smart", follow_redirects=True)
        assert response.status_code == 200

    def test_subject_filter_applied(self, client, db_session):
        teacher = create_test_user(db_session, "srteacher12", "teacher")
        for i in range(5):
            create_test_question(db_session, subject="数学", content=f"数学题{i}", created_by=teacher.id)
        for i in range(5):
            create_test_question(db_session, subject="英语", content=f"英语题{i}", created_by=teacher.id)
        user = create_test_user(db_session, "srstudent12", "student")
        db = TestingSessionLocal()
        try:
            result = _smart_select(user.id, db, subject="数学", count=5)
            for q, _ in result:
                assert q.subject == "数学"
        finally:
            db.close()
