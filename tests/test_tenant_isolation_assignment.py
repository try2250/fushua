"""多租户隔离测试 — Assignment 资源"""
import pytest
from fastapi.testclient import TestClient
from app.main import app as main_app
from app.models import User, ClassGroup, ClassMember, Assignment
from app.services.assignment_service import assignment_service
from app.core.security import create_access_token


def test_assignment_service_lists_only_tenant_assignments(db, teacher_a, teacher_b):
    cls_a = ClassGroup(name="A 班", created_by=teacher_a.id)
    cls_b = ClassGroup(name="B 班", created_by=teacher_b.id)
    db.add_all([cls_a, cls_b]); db.commit()
    db.refresh(cls_a); db.refresh(cls_b)
    db.add_all([
        Assignment(title="A 作业", question_ids="[1]",
                   created_by=teacher_a.id, class_id=cls_a.id),
        Assignment(title="B 作业", question_ids="[1]",
                   created_by=teacher_b.id, class_id=cls_b.id),
    ])
    db.commit()
    items = assignment_service.get_assignments_for_tenant(db, teacher_a.id)
    titles = {a.title for a in items}
    assert titles == {"A 作业"}


def test_assignment_by_id_cross_tenant_returns_none(db, teacher_a, teacher_b):
    cls_b = ClassGroup(name="B 班", created_by=teacher_b.id)
    db.add(cls_b); db.commit(); db.refresh(cls_b)
    a = Assignment(title="B", question_ids="[1]",
                   created_by=teacher_b.id, class_id=cls_b.id)
    db.add(a); db.commit(); db.refresh(a)
    got = assignment_service.get_assignment_by_id_for_tenant(db, teacher_a.id, a.id)
    assert got is None


# ─── Task 6: API CRUD tenant isolation ───


def test_api_list_assignments_isolated(db, teacher_a, teacher_b, teacher_a_token):
    cls_a = ClassGroup(name="A 班", created_by=teacher_a.id)
    cls_b = ClassGroup(name="B 班", created_by=teacher_b.id)
    db.add_all([cls_a, cls_b]); db.commit()
    db.refresh(cls_a); db.refresh(cls_b)
    db.add_all([
        Assignment(title="A 的", question_ids="[1]",
                   created_by=teacher_a.id, class_id=cls_a.id),
        Assignment(title="B 的", question_ids="[1]",
                   created_by=teacher_b.id, class_id=cls_b.id),
    ])
    db.commit()
    client = TestClient(main_app)
    r = client.get("/api/v1/assignments",
                   headers={"Authorization": f"Bearer {teacher_a_token}"})
    assert r.status_code == 200
    titles = [a["title"] for a in r.json()["data"]]
    assert titles == ["A 的"]


def test_api_get_assignment_detail_cross_tenant_returns_404(
    db, teacher_a, teacher_b, teacher_a_token
):
    cls_b = ClassGroup(name="B 班", created_by=teacher_b.id)
    db.add(cls_b); db.commit(); db.refresh(cls_b)
    a = Assignment(title="B", question_ids="[1]",
                   created_by=teacher_b.id, class_id=cls_b.id)
    db.add(a); db.commit(); db.refresh(a)
    client = TestClient(main_app)
    r = client.get(f"/api/v1/assignments/{a.id}",
                   headers={"Authorization": f"Bearer {teacher_a_token}"})
    assert r.status_code == 404


def test_create_assignment_assigns_tenant_as_created_by(
    db, teacher_a, teacher_a_token
):
    cls = ClassGroup(name="A 班", created_by=teacher_a.id)
    db.add(cls); db.commit(); db.refresh(cls)
    client = TestClient(main_app)
    r = client.post("/api/v1/assignments",
        headers={"Authorization": f"Bearer {teacher_a_token}"},
        json={"title": "新作业", "question_ids": "[1]",
              "class_id": cls.id, "description": ""})
    assert r.status_code == 200
    aid = r.json()["data"]["id"]
    a = db.query(Assignment).filter(Assignment.id == aid).first()
    assert a.created_by == teacher_a.id


def test_update_cross_tenant_assignment_returns_404(
    db, teacher_a, teacher_b, teacher_a_token
):
    cls_b = ClassGroup(name="B 班", created_by=teacher_b.id)
    db.add(cls_b); db.commit(); db.refresh(cls_b)
    a = Assignment(title="B", question_ids="[1]",
                   created_by=teacher_b.id, class_id=cls_b.id)
    db.add(a); db.commit(); db.refresh(a)
    client = TestClient(main_app)
    r = client.put(f"/api/v1/assignments/{a.id}",
        headers={"Authorization": f"Bearer {teacher_a_token}"},
        json={"title": "改"})
    assert r.status_code == 404


def test_delete_cross_tenant_assignment_returns_404(
    db, teacher_a, teacher_b, teacher_a_token
):
    cls_b = ClassGroup(name="B 班", created_by=teacher_b.id)
    db.add(cls_b); db.commit(); db.refresh(cls_b)
    a = Assignment(title="B", question_ids="[1]",
                   created_by=teacher_b.id, class_id=cls_b.id)
    db.add(a); db.commit(); db.refresh(a)
    client = TestClient(main_app)
    r = client.delete(f"/api/v1/assignments/{a.id}",
                      headers={"Authorization": f"Bearer {teacher_a_token}"})
    assert r.status_code == 404


# ─── Task 7: /submit + /records 学生场景 ───


def test_student_cannot_submit_cross_tenant_assignment(db, teacher_a, teacher_b):
    cls_a = ClassGroup(name="A 班", created_by=teacher_a.id)
    cls_b = ClassGroup(name="B 班", created_by=teacher_b.id)
    db.add_all([cls_a, cls_b]); db.commit()
    db.refresh(cls_a); db.refresh(cls_b)
    a_in_b = Assignment(title="B 的作业", question_ids="[1]",
                        created_by=teacher_b.id, class_id=cls_b.id)
    db.add(a_in_b); db.commit(); db.refresh(a_in_b)
    student = User(username="s_in_a", password_hash=User.hash_password("x"),
                   role="student", display_name="A 班学生")
    db.add(student); db.commit(); db.refresh(student)
    db.add(ClassMember(class_id=cls_a.id, user_id=student.id))
    db.commit()
    token = create_access_token({"user_id": student.id})
    client = TestClient(main_app)
    r = client.post(f"/api/v1/assignments/{a_in_b.id}/submit?class_id={cls_a.id}",
                    headers={"Authorization": f"Bearer {token}"},
                    json={"answers": {}})
    assert r.status_code == 404


def test_teacher_records_cross_tenant_returns_404(
    db, teacher_a, teacher_b, teacher_a_token
):
    cls_b = ClassGroup(name="B 班", created_by=teacher_b.id)
    db.add(cls_b); db.commit(); db.refresh(cls_b)
    a = Assignment(title="B 的", question_ids="[1]",
                   created_by=teacher_b.id, class_id=cls_b.id)
    db.add(a); db.commit(); db.refresh(a)
    client = TestClient(main_app)
    r = client.get(f"/api/v1/assignments/{a.id}/records",
                   headers={"Authorization": f"Bearer {teacher_a_token}"})
    assert r.status_code == 404
