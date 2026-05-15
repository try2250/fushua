import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import User, Question, Assignment, ClassGroup, ClassMember, AssignmentRecord
from tests.conftest import (
    create_test_user,
    create_test_question,
    get_csrf_token,
    login_as,
    register_and_login,
    TestingSessionLocal,
)


def _setup_teacher_class_student(client):
    db = TestingSessionLocal()
    try:
        teacher = create_test_user(db, "teacher_assign", "teacher")
        cls = ClassGroup(name="测试班级", created_by=teacher.id)
        db.add(cls)
        db.commit()
        db.refresh(cls)
        class_id = cls.id
        student = create_test_user(db, "student_assign", "student")
        student.class_id = class_id
        db.add(ClassMember(class_id=class_id, user_id=student.id))
        db.commit()
        db.refresh(student)
        q = create_test_question(db, created_by=teacher.id)
        question_id = q.id
        return teacher.id, class_id, student.id, question_id
    finally:
        db.close()


def test_create_assignment_requires_class_id(client):
    teacher_id, class_id, student_id, question_id = _setup_teacher_class_student(client)
    login_as(client, "teacher_assign")
    csrf = get_csrf_token(client)
    resp = client.post("/assignments/create", data={
        "title": "无班级作业",
        "description": "",
        "question_ids": str(question_id),
        "class_id": "",
        "_csrf_token": csrf,
    }, follow_redirects=False)
    assert resp.status_code != 303 or "error" in resp.text.lower()


def test_create_assignment_with_valid_class_id(client):
    teacher_id, class_id, student_id, question_id = _setup_teacher_class_student(client)
    login_as(client, "teacher_assign")
    csrf = get_csrf_token(client)
    resp = client.post("/assignments/create", data={
        "title": "有班级作业",
        "description": "",
        "question_ids": str(question_id),
        "class_id": str(class_id),
        "_csrf_token": csrf,
    }, follow_redirects=False)
    assert resp.status_code == 303
    db = TestingSessionLocal()
    try:
        assignment = db.query(Assignment).filter(Assignment.title == "有班级作业").first()
        assert assignment is not None
        assert assignment.class_id == class_id
    finally:
        db.close()


def test_create_assignment_with_other_teacher_class(client):
    db = TestingSessionLocal()
    try:
        teacher_a = create_test_user(db, "teacher_a_assign", "teacher")
        teacher_b = create_test_user(db, "teacher_b_assign", "teacher")
        cls_b = ClassGroup(name="教师B班级", created_by=teacher_b.id)
        db.add(cls_b)
        db.commit()
        db.refresh(cls_b)
        cls_b_id = cls_b.id
        q = create_test_question(db, created_by=teacher_a.id)
        q_id = q.id
    finally:
        db.close()

    login_as(client, "teacher_a_assign")
    csrf = get_csrf_token(client)
    resp = client.post("/assignments/create", data={
        "title": "越权作业",
        "description": "",
        "question_ids": str(q_id),
        "class_id": str(cls_b_id),
        "_csrf_token": csrf,
    }, follow_redirects=False)
    assert resp.status_code == 403


def test_complete_assignment_without_class_id_blocked(client):
    db = TestingSessionLocal()
    try:
        teacher = create_test_user(db, "teacher_noclass", "teacher")
        student = create_test_user(db, "student_noclass", "student")
        q = create_test_question(db, created_by=teacher.id)
        assignment = Assignment(
            title="无班级作业",
            question_ids=str(q.id),
            created_by=teacher.id,
            class_id=None,
        )
        db.add(assignment)
        db.commit()
        db.refresh(assignment)
        assignment_id = assignment.id
    finally:
        db.close()

    login_as(client, "student_noclass")
    csrf = get_csrf_token(client)
    resp = client.post(f"/assignments/{assignment_id}/complete", data={
        "_csrf_token": csrf,
    }, follow_redirects=False)
    assert resp.status_code == 403


def test_complete_assignment_with_class_membership(client):
    db = TestingSessionLocal()
    try:
        teacher = create_test_user(db, "teacher_cls", "teacher")
        cls = ClassGroup(name="完成班级", created_by=teacher.id)
        db.add(cls)
        db.commit()
        db.refresh(cls)
        cls_id = cls.id
        student = create_test_user(db, "student_cls", "student")
        student.class_id = cls_id
        db.add(ClassMember(class_id=cls_id, user_id=student.id))
        q = create_test_question(db, created_by=teacher.id)
        assignment = Assignment(
            title="班级作业",
            question_ids=str(q.id),
            created_by=teacher.id,
            class_id=cls_id,
        )
        db.add(assignment)
        db.commit()
        db.refresh(assignment)
        assignment_id = assignment.id
    finally:
        db.close()

    login_as(client, "student_cls")
    csrf = get_csrf_token(client)
    resp = client.post(f"/assignments/{assignment_id}/complete", data={
        "_csrf_token": csrf,
    }, follow_redirects=False)
    assert resp.status_code == 303


def test_complete_assignment_not_in_class(client):
    db = TestingSessionLocal()
    try:
        teacher = create_test_user(db, "teacher_notin", "teacher")
        cls = ClassGroup(name="其他班级", created_by=teacher.id)
        db.add(cls)
        db.commit()
        db.refresh(cls)
        cls_id = cls.id
        student = create_test_user(db, "student_notin", "student")
        q = create_test_question(db, created_by=teacher.id)
        assignment = Assignment(
            title="其他班作业",
            question_ids=str(q.id),
            created_by=teacher.id,
            class_id=cls_id,
        )
        db.add(assignment)
        db.commit()
        db.refresh(assignment)
        assignment_id = assignment.id
    finally:
        db.close()

    login_as(client, "student_notin")
    csrf = get_csrf_token(client)
    resp = client.post(f"/assignments/{assignment_id}/complete", data={
        "_csrf_token": csrf,
    }, follow_redirects=False)
    assert resp.status_code == 403


def test_teacher_only_sees_own_assignments(client):
    db = TestingSessionLocal()
    try:
        teacher_a = create_test_user(db, "ta_view", "teacher")
        teacher_b = create_test_user(db, "tb_view", "teacher")
        cls_a = ClassGroup(name="A班", created_by=teacher_a.id)
        cls_b = ClassGroup(name="B班", created_by=teacher_b.id)
        db.add_all([cls_a, cls_b])
        db.commit()
        db.refresh(cls_a)
        db.refresh(cls_b)
        q_a = create_test_question(db, created_by=teacher_a.id, content="A题")
        q_b = create_test_question(db, created_by=teacher_b.id, content="B题")
        a_a = Assignment(title="A作业", question_ids=str(q_a.id), created_by=teacher_a.id, class_id=cls_a.id)
        a_b = Assignment(title="B作业", question_ids=str(q_b.id), created_by=teacher_b.id, class_id=cls_b.id)
        db.add_all([a_a, a_b])
        db.commit()
    finally:
        db.close()

    login_as(client, "ta_view")
    resp = client.get("/teacher/assignments", follow_redirects=True)
    assert "A作业" in resp.text
    assert "B作业" not in resp.text


def test_teacher_cannot_view_other_teacher_assignment_detail(client):
    db = TestingSessionLocal()
    try:
        teacher_a = create_test_user(db, "ta_detail", "teacher")
        teacher_b = create_test_user(db, "tb_detail", "teacher")
        cls_b = ClassGroup(name="B班详情", created_by=teacher_b.id)
        db.add(cls_b)
        db.commit()
        db.refresh(cls_b)
        q_b = create_test_question(db, created_by=teacher_b.id, content="B题详情")
        a_b = Assignment(title="B作业详情", question_ids=str(q_b.id), created_by=teacher_b.id, class_id=cls_b.id)
        db.add(a_b)
        db.commit()
        db.refresh(a_b)
        assignment_id = a_b.id
    finally:
        db.close()

    login_as(client, "ta_detail")
    resp = client.get(f"/teacher/assignments/{assignment_id}", follow_redirects=False)
    assert resp.status_code == 404
