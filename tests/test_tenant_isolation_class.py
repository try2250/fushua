"""多租户隔离测试 — ClassGroup 资源"""
import pytest
from fastapi.testclient import TestClient
from app.main import app as main_app
from app.models import User, ClassGroup, ClassMember
from app.services.class_service import class_service
from app.core.security import create_access_token


def test_class_service_lists_only_tenant_classes(db, teacher_a, teacher_b):
    db.add_all([
        ClassGroup(name="A 的班 1", created_by=teacher_a.id),
        ClassGroup(name="A 的班 2", created_by=teacher_a.id),
        ClassGroup(name="B 的班", created_by=teacher_b.id),
    ])
    db.commit()
    classes = class_service.get_classes_for_tenant(db, teacher_a.id)
    names = {c.name for c in classes}
    assert names == {"A 的班 1", "A 的班 2"}


def test_class_service_get_by_id_cross_tenant_returns_none(db, teacher_a, teacher_b):
    cls = ClassGroup(name="B 的班", created_by=teacher_b.id)
    db.add(cls); db.commit(); db.refresh(cls)
    got = class_service.get_class_by_id_for_tenant(db, teacher_a.id, cls.id)
    assert got is None


# ─── Task 2: API list + detail tenant isolation ───


def test_api_list_classes_isolated_between_teachers(db, teacher_a, teacher_b, teacher_a_token):
    db.add_all([
        ClassGroup(name="A 的班", created_by=teacher_a.id),
        ClassGroup(name="B 的班", created_by=teacher_b.id),
    ])
    db.commit()
    client = TestClient(main_app)
    r = client.get("/api/v1/classes",
                   headers={"Authorization": f"Bearer {teacher_a_token}"})
    assert r.status_code == 200
    names = [c["name"] for c in r.json()["data"]]
    assert names == ["A 的班"]


def test_api_get_class_detail_cross_tenant_returns_404(
    db, teacher_a, teacher_b, teacher_a_token
):
    cls = ClassGroup(name="B 的班", created_by=teacher_b.id)
    db.add(cls); db.commit(); db.refresh(cls)
    client = TestClient(main_app)
    r = client.get(f"/api/v1/classes/{cls.id}",
                   headers={"Authorization": f"Bearer {teacher_a_token}"})
    assert r.status_code == 404


# ─── Task 3: API write ops tenant isolation ───


def test_create_class_assigns_tenant_as_created_by(db, teacher_a, teacher_a_token):
    client = TestClient(main_app)
    r = client.post("/api/v1/classes",
        headers={"Authorization": f"Bearer {teacher_a_token}"},
        json={"name": "新班"})
    assert r.status_code == 200
    created_id = r.json()["data"]["id"]
    c = db.query(ClassGroup).filter(ClassGroup.id == created_id).first()
    assert c.created_by == teacher_a.id


def test_update_cross_tenant_class_returns_404(db, teacher_a, teacher_b, teacher_a_token):
    cls = ClassGroup(name="B 的班", created_by=teacher_b.id)
    db.add(cls); db.commit(); db.refresh(cls)
    client = TestClient(main_app)
    r = client.put(f"/api/v1/classes/{cls.id}",
        headers={"Authorization": f"Bearer {teacher_a_token}"},
        json={"name": "改名"})
    assert r.status_code == 404


def test_delete_cross_tenant_class_returns_404(db, teacher_a, teacher_b, teacher_a_token):
    cls = ClassGroup(name="B 的班", created_by=teacher_b.id)
    db.add(cls); db.commit(); db.refresh(cls)
    client = TestClient(main_app)
    r = client.delete(f"/api/v1/classes/{cls.id}",
                      headers={"Authorization": f"Bearer {teacher_a_token}"})
    assert r.status_code == 404


# ─── Task 4: /join 学生跨租户入口 ───


def test_student_can_join_any_class_with_valid_token(db, teacher_b):
    cls = ClassGroup(name="B 的班", created_by=teacher_b.id)
    db.add(cls); db.commit(); db.refresh(cls)
    student = User(
        username="join_student",
        password_hash=User.hash_password("abc12345"),
        role="student",
        display_name="加入学生",
    )
    db.add(student); db.commit(); db.refresh(student)
    token = create_access_token({"user_id": student.id})

    client = TestClient(main_app)
    r = client.post(f"/api/v1/classes/{cls.id}/join",
                    headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert "成功" in r.json()["data"]["message"]


def test_join_nonexistent_class_returns_404(db):
    student = User(
        username="join_nope",
        password_hash=User.hash_password("abc12345"),
        role="student",
        display_name="x",
    )
    db.add(student); db.commit(); db.refresh(student)
    token = create_access_token({"user_id": student.id})
    client = TestClient(main_app)
    r = client.post("/api/v1/classes/99999/join",
                    headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 404
