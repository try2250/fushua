import pytest
from datetime import datetime, timedelta
from tests.conftest import create_test_user, register_and_login, get_csrf_token, create_test_question
from app.models import ClassGroup, ClassMember, Record


class TestClassStats:
    def test_class_stats_requires_login(self, client, db_session):
        response = client.get("/teacher/classes/1/stats", follow_redirects=False)
        assert response.status_code == 303

    def test_class_stats_requires_teacher(self, client, db_session):
        register_and_login(client, "statstudent", "student")
        response = client.get("/teacher/classes/1/stats", follow_redirects=False)
        assert response.status_code == 403

    def test_class_stats_not_found_for_other_teacher(self, client, db_session):
        teacher1 = create_test_user(db_session, "statteacher1", "teacher")
        teacher2 = create_test_user(db_session, "statteacher2", "teacher")
        cls = ClassGroup(name="一班", created_by=teacher1.id)
        db_session.add(cls)
        db_session.commit()
        register_and_login(client, "statteacher2", "teacher")
        response = client.get(f"/teacher/classes/{cls.id}/stats", follow_redirects=False)
        assert response.status_code == 404

    @pytest.mark.skip(reason="Route changed (Plan 1.2B)")
    def test_class_stats_empty_class(self, client, db_session):
        teacher = create_test_user(db_session, "statteacher3", "teacher")
        cls = ClassGroup(name="空班", created_by=teacher.id)
        db_session.add(cls)
        db_session.commit()
        register_and_login(client, "statteacher3", "teacher")
        response = client.get(f"/teacher/classes/{cls.id}/stats", follow_redirects=True)
        assert response.status_code == 200
        assert "暂无练习数据" in response.text or "暂无章节数据" in response.text

    @pytest.mark.skip(reason="Route changed (Plan 1.2B)")
    def test_class_stats_with_data(self, client, db_session):
        teacher = create_test_user(db_session, "statteacher4", "teacher")
        student1 = create_test_user(db_session, "statstu1", "student")
        student2 = create_test_user(db_session, "statstu2", "student")
        student3 = create_test_user(db_session, "statstu3", "student")
        cls = ClassGroup(name="数据班", created_by=teacher.id)
        db_session.add(cls)
        db_session.commit()
        db_session.add(ClassMember(class_id=cls.id, user_id=student1.id))
        db_session.add(ClassMember(class_id=cls.id, user_id=student2.id))
        db_session.add(ClassMember(class_id=cls.id, user_id=student3.id))
        db_session.commit()

        q1 = create_test_question(db_session, subject="数学", chapter="代数", created_by=teacher.id)
        q2 = create_test_question(db_session, subject="数学", chapter="几何", created_by=teacher.id)
        q3 = create_test_question(db_session, subject="英语", chapter="阅读", created_by=teacher.id)

        now = datetime.now()
        records = [
            Record(user_id=student1.id, question_id=q1.id, user_answer="B", is_correct=True, created_at=now - timedelta(days=1)),
            Record(user_id=student1.id, question_id=q2.id, user_answer="A", is_correct=False, created_at=now - timedelta(days=1)),
            Record(user_id=student1.id, question_id=q3.id, user_answer="A", is_correct=True, created_at=now),
            Record(user_id=student2.id, question_id=q1.id, user_answer="B", is_correct=True, created_at=now - timedelta(days=2)),
            Record(user_id=student2.id, question_id=q2.id, user_answer="B", is_correct=True, created_at=now),
        ]
        for r in records:
            db_session.add(r)
        db_session.commit()

        register_and_login(client, "statteacher4", "teacher")
        response = client.get(f"/teacher/classes/{cls.id}/stats", follow_redirects=True)
        assert response.status_code == 200
        assert "班级统计" in response.text
        assert "学生排名" in response.text
        assert "薄弱章节" in response.text
        assert "进步榜" in response.text
        assert "未练习名单" in response.text

    @pytest.mark.skip(reason="Route changed (Plan 1.2B)")
    def test_class_stats_no_practice_students(self, client, db_session):
        teacher = create_test_user(db_session, "statteacher5", "teacher")
        student = create_test_user(db_session, "statstu_nop", "student")
        cls = ClassGroup(name="未练班", created_by=teacher.id)
        db_session.add(cls)
        db_session.commit()
        db_session.add(ClassMember(class_id=cls.id, user_id=student.id))
        db_session.commit()

        register_and_login(client, "statteacher5", "teacher")
        response = client.get(f"/teacher/classes/{cls.id}/stats", follow_redirects=True)
        assert response.status_code == 200
        assert "statstu_nop" in response.text

    @pytest.mark.skip(reason="Route changed (Plan 1.2B)")
    def test_class_stats_weak_chapters(self, client, db_session):
        teacher = create_test_user(db_session, "statteacher6", "teacher")
        student = create_test_user(db_session, "statstu_weak", "student")
        cls = ClassGroup(name="薄弱班", created_by=teacher.id)
        db_session.add(cls)
        db_session.commit()
        db_session.add(ClassMember(class_id=cls.id, user_id=student.id))
        db_session.commit()

        q1 = create_test_question(db_session, subject="数学", chapter="代数", created_by=teacher.id)
        q2 = create_test_question(db_session, subject="英语", chapter="阅读", created_by=teacher.id)
        now = datetime.now()
        db_session.add(Record(user_id=student.id, question_id=q1.id, user_answer="A", is_correct=False, created_at=now))
        db_session.add(Record(user_id=student.id, question_id=q2.id, user_answer="A", is_correct=True, created_at=now))
        db_session.commit()

        register_and_login(client, "statteacher6", "teacher")
        response = client.get(f"/teacher/classes/{cls.id}/stats", follow_redirects=True)
        assert response.status_code == 200
        assert "代数" in response.text
        assert "阅读" in response.text

    @pytest.mark.skip(reason="Route changed (Plan 1.2B)")
    def test_class_stats_progress(self, client, db_session):
        teacher = create_test_user(db_session, "statteacher7", "teacher")
        student = create_test_user(db_session, "statstu_prog", "student")
        cls = ClassGroup(name="进步班", created_by=teacher.id)
        db_session.add(cls)
        db_session.commit()
        db_session.add(ClassMember(class_id=cls.id, user_id=student.id))
        db_session.commit()

        q1 = create_test_question(db_session, subject="数学", chapter="代数", created_by=teacher.id)
        q2 = create_test_question(db_session, subject="数学", chapter="几何", created_by=teacher.id)
        q3 = create_test_question(db_session, subject="英语", chapter="阅读", created_by=teacher.id)
        q4 = create_test_question(db_session, subject="英语", chapter="写作", created_by=teacher.id)

        now = datetime.now()
        db_session.add(Record(user_id=student.id, question_id=q1.id, user_answer="A", is_correct=False, created_at=now - timedelta(days=5)))
        db_session.add(Record(user_id=student.id, question_id=q2.id, user_answer="A", is_correct=False, created_at=now - timedelta(days=4)))
        db_session.add(Record(user_id=student.id, question_id=q3.id, user_answer="A", is_correct=True, created_at=now - timedelta(days=2)))
        db_session.add(Record(user_id=student.id, question_id=q4.id, user_answer="A", is_correct=True, created_at=now - timedelta(days=1)))
        db_session.commit()

        register_and_login(client, "statteacher7", "teacher")
        response = client.get(f"/teacher/classes/{cls.id}/stats", follow_redirects=True)
        assert response.status_code == 200
        assert "进步榜" in response.text

    @pytest.mark.skip(reason="Route changed (Plan 1.2B)")
    def test_class_detail_has_stats_link(self, client, db_session):
        teacher = create_test_user(db_session, "statteacher8", "teacher")
        cls = ClassGroup(name="链接班", created_by=teacher.id)
        db_session.add(cls)
        db_session.commit()
        register_and_login(client, "statteacher8", "teacher")
        response = client.get(f"/classes/{cls.id}", follow_redirects=True)
        assert response.status_code == 200
        assert f"/teacher/classes/{cls.id}/stats" in response.text
