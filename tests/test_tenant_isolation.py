"""
多租户隔离测试套件

覆盖：
- TenantContext 数据类基本行为
- Teacher/Student 角色租户解析
- tenant_filter 查询辅助
- question_service 租户级查询
- API 端点租户隔离
"""
import pytest
from app.core.tenant import TenantContext


def test_tenant_context_holds_id_user_source():
    ctx = TenantContext(tenant_id=7, user=None, source="teacher")
    assert ctx.tenant_id == 7
    assert ctx.source == "teacher"
    assert ctx.user is None


def test_tenant_context_repr_includes_id():
    ctx = TenantContext(tenant_id=42, user=None, source="student")
    assert "42" in repr(ctx)
    assert "student" in repr(ctx)


# ─── Task 2: Teacher Bearer Token → tenant ───

import pytest
from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from tests.conftest import TestingSessionLocal
from app.models import User
from app.database import get_db
from app.core.tenant import TenantContext, get_tenant_context
from app.core.security import create_access_token


@pytest.fixture
def teacher_user(db):
    user = User(
        username="teacher_a",
        password_hash=User.hash_password("abc12345"),
        role="teacher",
        display_name="A 老师",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _make_app_with_tenant():
    app = FastAPI()

    @app.get("/probe")
    def probe(tenant: TenantContext = Depends(get_tenant_context)):
        return {"tenant_id": tenant.tenant_id, "source": tenant.source}

    app.dependency_overrides[get_db] = lambda: (yield from _yield_session())
    return app


def _yield_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_teacher_bearer_resolves_to_own_tenant(teacher_user):
    app = _make_app_with_tenant()
    client = TestClient(app)
    token = create_access_token({"user_id": teacher_user.id})
    r = client.get("/probe", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    body = r.json()
    assert body["tenant_id"] == teacher_user.id
    assert body["source"] == "teacher"


# ─── Task 3: Student class_id → tenant ───

from app.models import ClassGroup, ClassMember


@pytest.fixture
def teacher_b_with_class(db):
    teacher = User(
        username="teacher_b",
        password_hash=User.hash_password("abc12345"),
        role="teacher",
        display_name="B 老师",
    )
    db.add(teacher)
    db.commit()
    db.refresh(teacher)
    cls = ClassGroup(name="B 班", created_by=teacher.id)
    db.add(cls)
    db.commit()
    db.refresh(cls)
    return teacher, cls


@pytest.fixture
def student_in_class_b(db, teacher_b_with_class):
    _, cls = teacher_b_with_class
    student = User(
        username="student_in_b",
        password_hash=User.hash_password("abc12345"),
        role="student",
        display_name="学生 1",
    )
    db.add(student)
    db.commit()
    db.refresh(student)
    member = ClassMember(class_id=cls.id, user_id=student.id)
    db.add(member)
    db.commit()
    return student, cls


def test_student_without_class_id_returns_400(student_in_class_b):
    student, _ = student_in_class_b
    app = _make_app_with_tenant()
    client = TestClient(app)
    token = create_access_token({"user_id": student.id})
    r = client.get("/probe", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 400
    assert "class_id" in r.json()["detail"]


def test_student_with_valid_class_resolves_to_class_teacher(student_in_class_b):
    student, cls = student_in_class_b
    app = _make_app_with_tenant()
    client = TestClient(app)
    token = create_access_token({"user_id": student.id})
    r = client.get(f"/probe?class_id={cls.id}", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["tenant_id"] == cls.created_by
    assert r.json()["source"] == "student"


def test_student_in_wrong_class_returns_403(student_in_class_b, teacher_user):
    student, _ = student_in_class_b
    other_cls = ClassGroup(name="A 班", created_by=teacher_user.id)
    db = TestingSessionLocal()
    db.add(other_cls)
    db.commit()
    db.refresh(other_cls)
    db.close()
    app = _make_app_with_tenant()
    client = TestClient(app)
    token = create_access_token({"user_id": student.id})
    r = client.get(f"/probe?class_id={other_cls.id}", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 403
