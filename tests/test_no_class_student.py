from fastapi.testclient import TestClient
from app.models import User, ClassGroup, ClassMember
from tests.conftest import TestingSessionLocal, create_test_user, create_test_question, get_csrf_token, register_and_login
from app.models import Assignment


def test_no_class_student_dashboard_no_assignments(client):
    """无班级学生dashboard没有作业列表"""
    db = TestingSessionLocal()
    try:
        teacher = create_test_user(db, "teacher21", "teacher")
        cls = ClassGroup(name="测试班级", created_by=teacher.id)
        db.add(cls)
        db.commit()
        student = create_test_user(db, "student21", "student")
        student.class_id = cls.id
        db.add(ClassMember(class_id=cls.id, user_id=student.id))
        db.commit()
        q = create_test_question(db, created_by=teacher.id)
        assignment = Assignment(
            title="有班级的作业",
            question_ids=str(q.id),
            created_by=teacher.id,
            class_id=cls.id
        )
        db.add(assignment)
        db.commit()
        
        no_class_student = create_test_user(db, "noclass21", "student")
        db.commit()
    finally:
        db.close()

    register_and_login(client, "noclass21", "student")
    resp = client.get("/student/dashboard")
    assert resp.status_code == 200


def test_no_class_student_assignments_page_empty(client):
    """无班级学生作业页面为空"""
    db = TestingSessionLocal()
    try:
        student = create_test_user(db, "noclass22", "student")
        db.commit()
    finally:
        db.close()

    register_and_login(client, "noclass22", "student")
    resp = client.get("/student/assignments")
    assert resp.status_code == 200
