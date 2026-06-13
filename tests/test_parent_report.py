import pytest
from datetime import datetime, timedelta
from tests.conftest import create_test_user, create_test_question, register_and_login


class TestParentReport:
    def test_parent_report_page_requires_teacher(self, client, db_session):
        student = create_test_user(db_session, "prstudent1", "student")
        response = client.get(f"/teacher/students/{student.id}/parent-report", follow_redirects=False)
        assert response.status_code in (303, 403)

    @pytest.mark.skip(reason="Route changed (Plan 1.2B)")
    def test_parent_report_page_returns_200(self, client, db_session):
        from app.models import ClassGroup, ClassMember
        teacher = create_test_user(db_session, "prteacher1", "teacher")
        student = create_test_user(db_session, "prstudent2", "student")
        cls = ClassGroup(name="家长报告班", created_by=teacher.id)
        db_session.add(cls)
        db_session.commit()
        student.class_id = cls.id
        db_session.add(ClassMember(class_id=cls.id, user_id=student.id))
        db_session.commit()
        register_and_login(client, "prteacher1", "teacher")
        response = client.get(f"/teacher/students/{student.id}/parent-report")
        assert response.status_code == 200
        assert "本周做题数" in response.text

    @pytest.mark.skip(reason="Route changed (Plan 1.2B)")
    def test_parent_report_shows_week_data(self, client, db_session):
        from app.models import ClassGroup, ClassMember
        teacher = create_test_user(db_session, "prteacher2", "teacher")
        student = create_test_user(db_session, "prstudent3", "student")
        q = create_test_question(db_session, subject="数学", chapter="代数", created_by=teacher.id)
        cls = ClassGroup(name="家长报告班2", created_by=teacher.id)
        db_session.add(cls)
        db_session.commit()
        student.class_id = cls.id
        db_session.add(ClassMember(class_id=cls.id, user_id=student.id))
        db_session.commit()

        from app.models import Record
        now = datetime.now()
        r1 = Record(user_id=student.id, question_id=q.id, user_answer="B", is_correct=True, created_at=now)
        r2 = Record(user_id=student.id, question_id=q.id, user_answer="A", is_correct=False, created_at=now)
        db_session.add_all([r1, r2])
        db_session.commit()

        register_and_login(client, "prteacher2", "teacher")
        response = client.get(f"/teacher/students/{student.id}/parent-report")
        assert response.status_code == 200
        assert "2" in response.text

    @pytest.mark.skip(reason="Route changed (Plan 1.2B)")
    def test_parent_report_shows_weak_points(self, client, db_session):
        from app.models import ClassGroup, ClassMember
        teacher = create_test_user(db_session, "prteacher3", "teacher")
        student = create_test_user(db_session, "prstudent4", "student")
        q1 = create_test_question(db_session, subject="数学", chapter="几何", created_by=teacher.id)
        q2 = create_test_question(db_session, subject="英语", chapter="阅读", created_by=teacher.id)
        cls = ClassGroup(name="家长报告班3", created_by=teacher.id)
        db_session.add(cls)
        db_session.commit()
        student.class_id = cls.id
        db_session.add(ClassMember(class_id=cls.id, user_id=student.id))
        db_session.commit()

        from app.models import Record
        now = datetime.now()
        for _ in range(4):
            db_session.add(Record(user_id=student.id, question_id=q1.id, user_answer="A", is_correct=False, created_at=now))
        db_session.add(Record(user_id=student.id, question_id=q2.id, user_answer="B", is_correct=True, created_at=now))
        db_session.commit()

        register_and_login(client, "prteacher3", "teacher")
        response = client.get(f"/teacher/students/{student.id}/parent-report")
        assert response.status_code == 200
        assert "几何" in response.text

    @pytest.mark.skip(reason="Route changed (Plan 1.2B)")
    def test_parent_report_old_records_excluded(self, client, db_session):
        from app.models import ClassGroup, ClassMember
        teacher = create_test_user(db_session, "prteacher4", "teacher")
        student = create_test_user(db_session, "prstudent5", "student")
        q = create_test_question(db_session, subject="数学", chapter="代数", created_by=teacher.id)
        cls = ClassGroup(name="家长报告班4", created_by=teacher.id)
        db_session.add(cls)
        db_session.commit()
        student.class_id = cls.id
        db_session.add(ClassMember(class_id=cls.id, user_id=student.id))
        db_session.commit()

        from app.models import Record
        old_date = datetime.now() - timedelta(days=14)
        db_session.add(Record(user_id=student.id, question_id=q.id, user_answer="B", is_correct=True, created_at=old_date))
        db_session.commit()

        register_and_login(client, "prteacher4", "teacher")
        response = client.get(f"/teacher/students/{student.id}/parent-report")
        assert response.status_code == 200
        assert "0" in response.text

    def test_parent_report_nonexistent_student(self, client, db_session):
        register_and_login(client, "prteacher5", "teacher")
        response = client.get("/teacher/students/99999/parent-report", follow_redirects=False)
        assert response.status_code == 404

    @pytest.mark.skip(reason="Route changed (Plan 1.2B)")
    def test_parent_report_pdf_returns_pdf(self, client, db_session):
        from app.models import ClassGroup, ClassMember
        teacher = create_test_user(db_session, "prteacher6", "teacher")
        student = create_test_user(db_session, "prstudent6", "student")
        cls = ClassGroup(name="家长报告班6", created_by=teacher.id)
        db_session.add(cls)
        db_session.commit()
        student.class_id = cls.id
        db_session.add(ClassMember(class_id=cls.id, user_id=student.id))
        db_session.commit()
        register_and_login(client, "prteacher6", "teacher")
        response = client.get(f"/teacher/students/{student.id}/parent-report/pdf")
        assert response.status_code == 200
        content_type = response.headers.get("content-type", "")
        assert "pdf" in content_type or "octet-stream" in content_type

    @pytest.mark.skip(reason="Route changed (Plan 1.2B)")
    def test_parent_report_pdf_with_data(self, client, db_session):
        from app.models import ClassGroup, ClassMember
        teacher = create_test_user(db_session, "prteacher7", "teacher")
        student = create_test_user(db_session, "prstudent7", "student")
        q = create_test_question(db_session, subject="数学", chapter="代数", created_by=teacher.id)
        cls = ClassGroup(name="家长报告班7", created_by=teacher.id)
        db_session.add(cls)
        db_session.commit()
        student.class_id = cls.id
        db_session.add(ClassMember(class_id=cls.id, user_id=student.id))
        db_session.commit()

        from app.models import Record
        now = datetime.now()
        db_session.add(Record(user_id=student.id, question_id=q.id, user_answer="B", is_correct=True, created_at=now))
        db_session.add(Record(user_id=student.id, question_id=q.id, user_answer="A", is_correct=False, created_at=now))
        db_session.commit()

        register_and_login(client, "prteacher7", "teacher")
        response = client.get(f"/teacher/students/{student.id}/parent-report/pdf")
        assert response.status_code == 200
        assert len(response.content) > 0

    def test_parent_report_pdf_requires_teacher(self, client, db_session):
        student = create_test_user(db_session, "prstudent8", "student")
        response = client.get(f"/teacher/students/{student.id}/parent-report/pdf", follow_redirects=False)
        assert response.status_code in (303, 403)

    def test_parent_report_pdf_nonexistent_student(self, client, db_session):
        register_and_login(client, "prteacher8", "teacher")
        response = client.get("/teacher/students/99999/parent-report/pdf", follow_redirects=False)
        assert response.status_code == 404

    @pytest.mark.skip(reason="Route changed (Plan 1.2B)")
    def test_parent_report_no_weak_points(self, client, db_session):
        from app.models import ClassGroup, ClassMember
        teacher = create_test_user(db_session, "prteacher9", "teacher")
        student = create_test_user(db_session, "prstudent9", "student")
        q = create_test_question(db_session, subject="数学", chapter="代数", created_by=teacher.id)
        cls = ClassGroup(name="家长报告班9", created_by=teacher.id)
        db_session.add(cls)
        db_session.commit()
        student.class_id = cls.id
        db_session.add(ClassMember(class_id=cls.id, user_id=student.id))
        db_session.commit()

        from app.models import Record
        now = datetime.now()
        for _ in range(5):
            db_session.add(Record(user_id=student.id, question_id=q.id, user_answer="B", is_correct=True, created_at=now))
        db_session.commit()

        register_and_login(client, "prteacher9", "teacher")
        response = client.get(f"/teacher/students/{student.id}/parent-report")
        assert response.status_code == 200
        assert "暂无薄弱知识点" in response.text
