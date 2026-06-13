import pytest
from datetime import datetime, timedelta
from app.models import (
    User, Question, Record, ClassGroup, ClassMember, Assignment,
    AssignmentRecord, AuditLog, QuestionBank, Notification, MasteryRecord,
)
from tests.conftest import (
    create_test_user, create_test_question, login_as, register_and_login,
    get_csrf_token, TestingSessionLocal,
)


class TestPhase1AssignmentIsolation:
    def test_student_dashboard_only_shows_own_class_assignments(self, client, db_session):
        teacher = create_test_user(db_session, "teacher1", "teacher")
        cls_a = ClassGroup(name="A班", created_by=teacher.id)
        cls_b = ClassGroup(name="B班", created_by=teacher.id)
        db_session.add_all([cls_a, cls_b])
        db_session.commit()

        q1 = create_test_question(db_session, "数学", created_by=teacher.id)
        q2 = create_test_question(db_session, "英语", created_by=teacher.id)

        a1 = Assignment(title="A班作业", question_ids=str(q1.id), created_by=teacher.id, class_id=cls_a.id)
        a2 = Assignment(title="B班作业", question_ids=str(q2.id), created_by=teacher.id, class_id=cls_b.id)
        db_session.add_all([a1, a2])
        db_session.commit()

        student_a = create_test_user(db_session, "student_a", "student")
        student_a.class_id = cls_a.id
        db_session.add(ClassMember(class_id=cls_a.id, user_id=student_a.id))
        db_session.commit()

        login_as(client, "student_a")
        resp = client.get("/student/dashboard", follow_redirects=True)
        assert resp.status_code == 200
        assert "A班作业" in resp.text
        assert "B班作业" not in resp.text

    def test_student_cannot_complete_other_class_assignment(self, client, db_session):
        teacher = create_test_user(db_session, "teacher1", "teacher")
        cls_a = ClassGroup(name="A班", created_by=teacher.id)
        cls_b = ClassGroup(name="B班", created_by=teacher.id)
        db_session.add_all([cls_a, cls_b])
        db_session.commit()

        q = create_test_question(db_session, "数学", created_by=teacher.id)
        a = Assignment(title="B班作业", question_ids=str(q.id), created_by=teacher.id, class_id=cls_b.id)
        db_session.add(a)
        db_session.commit()

        student_a = create_test_user(db_session, "student_a", "student")
        student_a.class_id = cls_a.id
        db_session.add(ClassMember(class_id=cls_a.id, user_id=student_a.id))
        db_session.commit()

        login_as(client, "student_a")
        csrf = get_csrf_token(client)
        resp = client.post(f"/assignments/{a.id}/complete", data={"_csrf_token": csrf}, follow_redirects=False)
        assert resp.status_code == 403

    def test_create_assignment_requires_class_id(self, client, db_session):
        teacher = create_test_user(db_session, "teacher1", "teacher")
        login_as(client, "teacher1")
        csrf = get_csrf_token(client)
        q = create_test_question(db_session, "数学", created_by=teacher.id)
        resp = client.post("/assignments/create", data={
            "title": "无班级作业",
            "question_ids": str(q.id),
            "class_id": "",
            "_csrf_token": csrf,
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert "请选择班级" in resp.text

    def test_assignment_without_class_id_cannot_be_completed(self, client, db_session):
        teacher = create_test_user(db_session, "teacher1", "teacher")
        cls = ClassGroup(name="测试班", created_by=teacher.id)
        db_session.add(cls)
        db_session.commit()

        q = create_test_question(db_session, "数学", created_by=teacher.id)
        a = Assignment(title="无班级作业", question_ids=str(q.id), created_by=teacher.id, class_id=None)
        db_session.add(a)
        db_session.commit()

        student = create_test_user(db_session, "student1", "student")
        student.class_id = cls.id
        db_session.add(ClassMember(class_id=cls.id, user_id=student.id))
        db_session.commit()

        login_as(client, "student1")
        csrf = get_csrf_token(client)
        resp = client.post(f"/assignments/{a.id}/complete", data={"_csrf_token": csrf}, follow_redirects=False)
        assert resp.status_code == 403

    def test_teacher_owns_student_check(self, client, db_session):
        teacher_a = create_test_user(db_session, "teacher_a", "teacher")
        teacher_b = create_test_user(db_session, "teacher_b", "teacher")
        cls_a = ClassGroup(name="A班", created_by=teacher_a.id)
        db_session.add(cls_a)
        db_session.commit()

        student = create_test_user(db_session, "student1", "student")
        student.class_id = cls_a.id
        db_session.add(ClassMember(class_id=cls_a.id, user_id=student.id))
        db_session.commit()

        login_as(client, "teacher_b")
        resp = client.get(f"/teacher/students/{student.id}", follow_redirects=False)
        assert resp.status_code == 404


class TestPhase2DataConsistency:
    def test_no_class_student_sees_friendly_message(self, client, db_session):
        student = create_test_user(db_session, "noclass_student", "student")
        student.class_id = None
        db_session.commit()

        login_as(client, "noclass_student")
        resp = client.get("/student/assignments", follow_redirects=True)
        assert resp.status_code == 200
        assert "还没有加入班级" in resp.text or "暂无作业" in resp.text

    def test_assignment_delete_cascades_records(self, client, db_session):
        teacher = create_test_user(db_session, "teacher1", "teacher")
        cls = ClassGroup(name="测试班", created_by=teacher.id)
        db_session.add(cls)
        db_session.commit()

        q = create_test_question(db_session, "数学", created_by=teacher.id)
        a = Assignment(title="待删作业", question_ids=str(q.id), created_by=teacher.id, class_id=cls.id)
        db_session.add(a)
        db_session.commit()

        student = create_test_user(db_session, "student1", "student")
        student.class_id = cls.id
        db_session.add(ClassMember(class_id=cls.id, user_id=student.id))
        db_session.add(AssignmentRecord(assignment_id=a.id, user_id=student.id, completed=True, completed_at=datetime.now()))
        db_session.commit()

        assert db_session.query(AssignmentRecord).filter(AssignmentRecord.assignment_id == a.id).count() == 1

        login_as(client, "teacher1")
        csrf = get_csrf_token(client)
        resp = client.post(f"/teacher/assignments/{a.id}/delete", data={"_csrf_token": csrf}, follow_redirects=False)
        assert resp.status_code == 303
        assert db_session.query(AssignmentRecord).filter(AssignmentRecord.assignment_id == a.id).count() == 0

    def test_admin_can_view_any_student(self, client, db_session):
        teacher = create_test_user(db_session, "teacher1", "teacher")
        admin = create_test_user(db_session, "admin1", "admin")
        admin.is_admin = True
        db_session.commit()

        cls = ClassGroup(name="测试班", created_by=teacher.id)
        db_session.add(cls)
        db_session.commit()

        student = create_test_user(db_session, "student1", "student")
        student.class_id = cls.id
        db_session.add(ClassMember(class_id=cls.id, user_id=student.id))
        db_session.commit()

        login_as(client, "admin1")
        resp = client.get(f"/teacher/students/{student.id}", follow_redirects=False)
        assert resp.status_code == 200


class TestPhase3OpsMonitoring:
    def test_audit_log_created_on_assignment_create(self, client, db_session):
        teacher = create_test_user(db_session, "teacher1", "teacher")
        cls = ClassGroup(name="测试班", created_by=teacher.id)
        db_session.add(cls)
        db_session.commit()

        q = create_test_question(db_session, "数学", created_by=teacher.id)

        login_as(client, "teacher1")
        csrf = get_csrf_token(client)
        resp = client.post("/assignments/create", data={
            "title": "审计测试作业",
            "question_ids": str(q.id),
            "class_id": str(cls.id),
            "_csrf_token": csrf,
        }, follow_redirects=False)
        assert resp.status_code == 303

        log = db_session.query(AuditLog).filter(AuditLog.action == "create_assignment").first()
        assert log is not None
        assert "审计测试作业" in log.detail

    def test_audit_log_created_on_assignment_delete(self, client, db_session):
        teacher = create_test_user(db_session, "teacher1", "teacher")
        cls = ClassGroup(name="测试班", created_by=teacher.id)
        db_session.add(cls)
        db_session.commit()

        q = create_test_question(db_session, "数学", created_by=teacher.id)
        a = Assignment(title="待删作业", question_ids=str(q.id), created_by=teacher.id, class_id=cls.id)
        db_session.add(a)
        db_session.commit()

        login_as(client, "teacher1")
        csrf = get_csrf_token(client)
        client.post(f"/teacher/assignments/{a.id}/delete", data={"_csrf_token": csrf}, follow_redirects=False)

        log = db_session.query(AuditLog).filter(AuditLog.action == "delete_assignment").first()
        assert log is not None
        assert "待删作业" in log.detail

    def test_audit_log_created_on_remove_member(self, client, db_session):
        teacher = create_test_user(db_session, "teacher1", "teacher")
        cls = ClassGroup(name="测试班", created_by=teacher.id)
        db_session.add(cls)
        db_session.commit()

        student = create_test_user(db_session, "student1", "student")
        db_session.add(ClassMember(class_id=cls.id, user_id=student.id))
        db_session.commit()

        login_as(client, "teacher1")
        csrf = get_csrf_token(client)
        client.post(f"/classes/{cls.id}/members/{student.id}/remove", data={"_csrf_token": csrf}, follow_redirects=False)

        log = db_session.query(AuditLog).filter(AuditLog.action == "remove_member").first()
        assert log is not None

    def test_audit_log_created_on_delete_class(self, client, db_session):
        teacher = create_test_user(db_session, "teacher1", "teacher")
        cls = ClassGroup(name="待删班级", created_by=teacher.id)
        db_session.add(cls)
        db_session.commit()

        login_as(client, "teacher1")
        csrf = get_csrf_token(client)
        client.post(f"/classes/{cls.id}/delete", data={"_csrf_token": csrf}, follow_redirects=False)

        log = db_session.query(AuditLog).filter(AuditLog.action == "delete_class").first()
        assert log is not None
        assert "待删班级" in log.detail

    def test_audit_log_created_on_delete_question(self, client, db_session):
        teacher = create_test_user(db_session, "teacher1", "teacher")
        q = create_test_question(db_session, "数学", created_by=teacher.id, content="待删题目内容")

        login_as(client, "teacher1")
        csrf = get_csrf_token(client)
        client.post(f"/teacher/questions/{q.id}/delete", data={"_csrf_token": csrf}, follow_redirects=False)

        log = db_session.query(AuditLog).filter(AuditLog.action == "delete_question").first()
        assert log is not None

    def test_audit_log_created_on_delete_bank(self, client, db_session):
        teacher = create_test_user(db_session, "teacher1", "teacher")
        bank = QuestionBank(name="待删题库", subject="数学", created_by=teacher.id)
        db_session.add(bank)
        db_session.commit()

        login_as(client, "teacher1")
        csrf = get_csrf_token(client)
        client.post(f"/teacher/banks/{bank.id}/delete", data={"_csrf_token": csrf}, follow_redirects=False)

        log = db_session.query(AuditLog).filter(AuditLog.action == "delete_bank").first()
        assert log is not None
        assert "待删题库" in log.detail

    def test_health_endpoint_detailed(self, client, db_session):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert "checks" in data
        assert data["checks"]["database"] == "ok"
        assert "user_count" in data["checks"]
        assert "version" in data["checks"]

    def test_admin_audit_log_page_accessible(self, client, db_session):
        admin = create_test_user(db_session, "admin1", "admin")
        admin.is_admin = True
        db_session.commit()

        login_as(client, "admin1")
        resp = client.get("/admin/audit-log", follow_redirects=True)
        assert resp.status_code == 200

    def test_admin_audit_log_export(self, client, db_session):
        admin = create_test_user(db_session, "admin1", "admin")
        admin.is_admin = True
        db_session.commit()

        db_session.add(AuditLog(actor_id=admin.id, action="test_action", target_type="test", detail="测试审计日志"))
        db_session.commit()

        login_as(client, "admin1")
        resp = client.get("/admin/audit-log/export", follow_redirects=False)
        assert resp.status_code == 200
        assert "text/csv" in resp.headers.get("content-type", "")

    def test_non_admin_cannot_access_audit_log(self, client, db_session):
        teacher = create_test_user(db_session, "teacher1", "teacher")
        login_as(client, "teacher1")
        resp = client.get("/admin/audit-log", follow_redirects=False)
        assert resp.status_code in (303, 403)


class TestPhase4UserExperience:
    def test_teacher_questions_pagination(self, client, db_session):
        teacher = create_test_user(db_session, "teacher1", "teacher")
        for i in range(25):
            create_test_question(db_session, "数学", created_by=teacher.id, content=f"题目{i+1}")

        login_as(client, "teacher1")
        resp = client.get("/teacher/questions?page=1", follow_redirects=True)
        assert resp.status_code == 200

        resp2 = client.get("/teacher/questions?page=2", follow_redirects=True)
        assert resp2.status_code == 200

    def test_student_records_pagination(self, client, db_session):
        teacher = create_test_user(db_session, "teacher1", "teacher")
        student = create_test_user(db_session, "student1", "student")
        cls = ClassGroup(name="测试班", created_by=teacher.id)
        db_session.add(cls)
        db_session.commit()
        student.class_id = cls.id
        db_session.add(ClassMember(class_id=cls.id, user_id=student.id))
        db_session.commit()

        for i in range(25):
            q = create_test_question(db_session, "数学", created_by=teacher.id, content=f"题目{i+1}")
            db_session.add(Record(user_id=student.id, question_id=q.id, user_answer="A", is_correct=True))
        db_session.commit()

        login_as(client, "student1")
        resp = client.get("/student/records?page=1", follow_redirects=True)
        assert resp.status_code == 200

        resp2 = client.get("/student/records?page=2", follow_redirects=True)
        assert resp2.status_code == 200

    def test_teacher_assignments_pagination(self, client, db_session):
        teacher = create_test_user(db_session, "teacher1", "teacher")
        cls = ClassGroup(name="测试班", created_by=teacher.id)
        db_session.add(cls)
        db_session.commit()

        q = create_test_question(db_session, "数学", created_by=teacher.id)
        for i in range(20):
            db_session.add(Assignment(title=f"作业{i+1}", question_ids=str(q.id), created_by=teacher.id, class_id=cls.id))
        db_session.commit()

        login_as(client, "teacher1")
        resp = client.get("/teacher/assignments?page=1", follow_redirects=True)
        assert resp.status_code == 200

    def test_student_assignments_pagination(self, client, db_session):
        teacher = create_test_user(db_session, "teacher1", "teacher")
        cls = ClassGroup(name="测试班", created_by=teacher.id)
        db_session.add(cls)
        db_session.commit()

        student = create_test_user(db_session, "student1", "student")
        student.class_id = cls.id
        db_session.add(ClassMember(class_id=cls.id, user_id=student.id))
        db_session.commit()

        q = create_test_question(db_session, "数学", created_by=teacher.id)
        for i in range(20):
            db_session.add(Assignment(title=f"作业{i+1}", question_ids=str(q.id), created_by=teacher.id, class_id=cls.id))
        db_session.commit()

        login_as(client, "student1")
        resp = client.get("/student/assignments?page=1", follow_redirects=True)
        assert resp.status_code == 200

    def test_error_page_safe_details(self, client, db_session):
        teacher = create_test_user(db_session, "teacher1", "teacher")
        login_as(client, "teacher1")
        resp = client.get("/teacher/students/99999", follow_redirects=False)
        assert resp.status_code == 404
        assert "操作失败" not in resp.text or "学生不存在" in resp.text or "页面未找到" in resp.text

    def test_error_page_has_back_button(self, client, db_session):
        resp = client.get("/nonexistent-page-12345", follow_redirects=False)
        assert resp.status_code == 404
        assert "返回上一页" in resp.text

    def test_student_management_member_limit(self, client, db_session):
        teacher = create_test_user(db_session, "teacher1", "teacher")
        cls = ClassGroup(name="大班", created_by=teacher.id)
        db_session.add(cls)
        db_session.commit()

        for i in range(25):
            s = create_test_user(db_session, f"student_{i}", "student")
            s.class_id = cls.id
            db_session.add(ClassMember(class_id=cls.id, user_id=s.id))
        db_session.commit()

        login_as(client, "teacher1")
        resp = client.get("/teacher/students", follow_redirects=True)
        assert resp.status_code == 200
        assert "25" in resp.text
        assert "查看全部" in resp.text


class TestCrossPhaseSecurity:
    def test_cross_teacher_cannot_delete_other_assignment(self, client, db_session):
        teacher_a = create_test_user(db_session, "teacher_a", "teacher")
        teacher_b = create_test_user(db_session, "teacher_b", "teacher")
        cls_a = ClassGroup(name="A班", created_by=teacher_a.id)
        db_session.add(cls_a)
        db_session.commit()

        q = create_test_question(db_session, "数学", created_by=teacher_a.id)
        a = Assignment(title="A的作业", question_ids=str(q.id), created_by=teacher_a.id, class_id=cls_a.id)
        db_session.add(a)
        db_session.commit()

        login_as(client, "teacher_b")
        csrf = get_csrf_token(client)
        resp = client.post(f"/teacher/assignments/{a.id}/delete", data={"_csrf_token": csrf}, follow_redirects=False)
        assert resp.status_code == 404
        assert db_session.query(Assignment).filter(Assignment.id == a.id).first() is not None

    def test_cross_teacher_cannot_view_other_class_detail(self, client, db_session):
        teacher_a = create_test_user(db_session, "teacher_a", "teacher")
        teacher_b = create_test_user(db_session, "teacher_b", "teacher")
        cls_a = ClassGroup(name="A班", created_by=teacher_a.id)
        db_session.add(cls_a)
        db_session.commit()

        login_as(client, "teacher_b")
        resp = client.get(f"/classes/{cls_a.id}", follow_redirects=False)
        assert resp.status_code == 404

    def test_cross_teacher_cannot_add_member_to_other_class(self, client, db_session):
        teacher_a = create_test_user(db_session, "teacher_a", "teacher")
        teacher_b = create_test_user(db_session, "teacher_b", "teacher")
        cls_a = ClassGroup(name="A班", created_by=teacher_a.id)
        db_session.add(cls_a)
        db_session.commit()

        student = create_test_user(db_session, "student1", "student")

        login_as(client, "teacher_b")
        csrf = get_csrf_token(client)
        resp = client.post(f"/classes/{cls_a.id}/members/add", data={
            "username": "student1",
            "_csrf_token": csrf,
        }, follow_redirects=False)
        assert resp.status_code == 404

    def test_pagination_invalid_page_defaults_to_1(self, client, db_session):
        teacher = create_test_user(db_session, "teacher1", "teacher")
        create_test_question(db_session, "数学", created_by=teacher.id)

        login_as(client, "teacher1")
        resp = client.get("/teacher/questions?page=-1", follow_redirects=True)
        assert resp.status_code == 200

        resp2 = client.get("/teacher/questions?page=abc", follow_redirects=True)
        assert resp2.status_code == 200

    def test_pagination_beyond_last_page(self, client, db_session):
        teacher = create_test_user(db_session, "teacher1", "teacher")
        create_test_question(db_session, "数学", created_by=teacher.id)

        login_as(client, "teacher1")
        resp = client.get("/teacher/questions?page=999", follow_redirects=True)
        assert resp.status_code == 200


class TestBugHuntEdgeCases:
    def test_assignment_detail_no_class_id_shows_empty_students(self, client, db_session):
        teacher = create_test_user(db_session, "teacher1", "teacher")
        q = create_test_question(db_session, "数学", created_by=teacher.id)
        a = Assignment(title="无班级作业", question_ids=str(q.id), created_by=teacher.id, class_id=None)
        db_session.add(a)
        db_session.commit()

        login_as(client, "teacher1")
        resp = client.get(f"/teacher/assignments/{a.id}", follow_redirects=True)
        assert resp.status_code == 200

    def test_delete_class_clears_student_class_id(self, client, db_session):
        teacher = create_test_user(db_session, "teacher1", "teacher")
        cls = ClassGroup(name="待删班", created_by=teacher.id)
        db_session.add(cls)
        db_session.commit()

        student = create_test_user(db_session, "student1", "student")
        student.class_id = cls.id
        db_session.add(ClassMember(class_id=cls.id, user_id=student.id))
        db_session.commit()

        assert student.class_id == cls.id

        login_as(client, "teacher1")
        csrf = get_csrf_token(client)
        client.post(f"/classes/{cls.id}/delete", data={"_csrf_token": csrf}, follow_redirects=False)

        db_session.refresh(student)
        assert student.class_id is None

    def test_remove_member_clears_class_id(self, client, db_session):
        teacher = create_test_user(db_session, "teacher1", "teacher")
        cls = ClassGroup(name="测试班", created_by=teacher.id)
        db_session.add(cls)
        db_session.commit()

        student = create_test_user(db_session, "student1", "student")
        student.class_id = cls.id
        db_session.add(ClassMember(class_id=cls.id, user_id=student.id))
        db_session.commit()

        login_as(client, "teacher1")
        csrf = get_csrf_token(client)
        client.post(f"/classes/{cls.id}/members/{student.id}/remove", data={"_csrf_token": csrf}, follow_redirects=False)

        db_session.refresh(student)
        assert student.class_id is None

    def test_student_assignments_no_class_empty_query(self, client, db_session):
        student = create_test_user(db_session, "noclass_student", "student")
        student.class_id = None
        db_session.commit()

        login_as(client, "noclass_student")
        resp = client.get("/student/assignments", follow_redirects=True)
        assert resp.status_code == 200

    def test_audit_log_page_non_admin_redirect(self, client, db_session):
        teacher = create_test_user(db_session, "teacher1", "teacher")
        login_as(client, "teacher1")
        resp = client.get("/admin/audit-log", follow_redirects=False)
        assert resp.status_code in (303, 403)

    def test_audit_log_export_non_admin(self, client, db_session):
        teacher = create_test_user(db_session, "teacher1", "teacher")
        login_as(client, "teacher1")
        resp = client.get("/admin/audit-log/export", follow_redirects=False)
        assert resp.status_code in (303, 403)

    def test_teacher_questions_filter_with_pagination(self, client, db_session):
        teacher = create_test_user(db_session, "teacher1", "teacher")
        for i in range(25):
            create_test_question(db_session, "数学", created_by=teacher.id, content=f"数学题{i+1}")
        for i in range(5):
            create_test_question(db_session, "英语", created_by=teacher.id, content=f"英语题{i+1}")

        login_as(client, "teacher1")
        resp = client.get("/teacher/questions?subject=数学&page=1", follow_redirects=True)
        assert resp.status_code == 200
        assert "数学" in resp.text

    def test_admin_can_delete_any_assignment(self, client, db_session):
        teacher = create_test_user(db_session, "teacher1", "teacher")
        admin = create_test_user(db_session, "admin1", "admin")
        admin.is_admin = True
        db_session.commit()

        cls = ClassGroup(name="测试班", created_by=teacher.id)
        db_session.add(cls)
        db_session.commit()

        q = create_test_question(db_session, "数学", created_by=teacher.id)
        a = Assignment(title="教师作业", question_ids=str(q.id), created_by=teacher.id, class_id=cls.id)
        db_session.add(a)
        db_session.commit()

        login_as(client, "admin1")
        csrf = get_csrf_token(client)
        resp = client.post(f"/teacher/assignments/{a.id}/delete", data={"_csrf_token": csrf}, follow_redirects=False)
        assert resp.status_code == 303
        assert db_session.query(Assignment).filter(Assignment.id == a.id).first() is None

    def test_safe_details_whitelist_in_error_handler(self, client, db_session):
        teacher = create_test_user(db_session, "teacher1", "teacher")
        cls = ClassGroup(name="测试班", created_by=teacher.id)
        db_session.add(cls)
        db_session.commit()

        student = create_test_user(db_session, "student1", "student")
        student.class_id = cls.id
        db_session.add(ClassMember(class_id=cls.id, user_id=student.id))
        db_session.commit()

        q = create_test_question(db_session, "数学", created_by=teacher.id)
        a = Assignment(title="无班级作业", question_ids=str(q.id), created_by=teacher.id, class_id=None)
        db_session.add(a)
        db_session.commit()

        login_as(client, "student1")
        csrf = get_csrf_token(client)
        resp = client.post(f"/assignments/{a.id}/complete", data={"_csrf_token": csrf}, follow_redirects=False)
        assert resp.status_code == 403
        assert "该作业未绑定班级" in resp.text

    def test_student_dashboard_with_class_shows_assignments(self, client, db_session):
        teacher = create_test_user(db_session, "teacher1", "teacher")
        cls = ClassGroup(name="测试班", created_by=teacher.id)
        db_session.add(cls)
        db_session.commit()

        q = create_test_question(db_session, "数学", created_by=teacher.id)
        a = Assignment(title="班级作业", question_ids=str(q.id), created_by=teacher.id, class_id=cls.id)
        db_session.add(a)
        db_session.commit()

        student = create_test_user(db_session, "student1", "student")
        student.class_id = cls.id
        db_session.add(ClassMember(class_id=cls.id, user_id=student.id))
        db_session.commit()

        login_as(client, "student1")
        resp = client.get("/student/dashboard", follow_redirects=True)
        assert resp.status_code == 200
        assert "班级作业" in resp.text
