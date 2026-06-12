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
from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient

from app.core.tenant import TenantContext, get_tenant_context, tenant_filter
from app.core.security import create_access_token
from app.database import get_db
from app.main import app as main_app
from app.models import User, Question, ClassGroup, ClassMember
from app.services.question_service import question_service
from tests.conftest import TestingSessionLocal


# ─── Task 1: TenantContext dataclass ───

def test_tenant_context_holds_id_user_source():
    ctx = TenantContext(tenant_id=7, user=None, source="teacher")
    assert ctx.tenant_id == 7
    assert ctx.source == "teacher"
    assert ctx.user is None


def test_tenant_context_repr_includes_id():
    ctx = TenantContext(tenant_id=42, user=None, source="student")
    assert "42" in repr(ctx)
    assert "student" in repr(ctx)


# ─── Shared helpers for Task 2-3 (tenant probe app) ───

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


# ─── Task 2: Teacher Bearer Token → tenant ───

def test_teacher_bearer_resolves_to_own_tenant(teacher_a):
    app = _make_app_with_tenant()
    client = TestClient(app)
    token = create_access_token({"user_id": teacher_a.id})
    r = client.get("/probe", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    body = r.json()
    assert body["tenant_id"] == teacher_a.id
    assert body["source"] == "teacher"


# ─── Task 3: Student class_id → tenant ───

def test_student_without_class_id_returns_400(class_b_with_student):
    _, student = class_b_with_student
    app = _make_app_with_tenant()
    client = TestClient(app)
    token = create_access_token({"user_id": student.id})
    r = client.get("/probe", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 400
    assert "class_id" in r.json()["detail"]


def test_student_with_valid_class_resolves_to_class_teacher(class_b_with_student):
    cls, student = class_b_with_student
    app = _make_app_with_tenant()
    client = TestClient(app)
    token = create_access_token({"user_id": student.id})
    r = client.get(f"/probe?class_id={cls.id}", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["tenant_id"] == cls.created_by
    assert r.json()["source"] == "student"


def test_student_in_wrong_class_returns_403(class_b_with_student, teacher_a):
    _, student = class_b_with_student
    other_cls = ClassGroup(name="A 班", created_by=teacher_a.id)
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


# ─── Task 4: tenant_filter query helper ───

def test_tenant_filter_applies_created_by(db, teacher_a, teacher_b):
    q1 = Question(subject="数学", semester="七年级上册", chapter="代数",
                  q_type="choice", content="题 1", answer="A",
                  created_by=teacher_a.id)
    q2 = Question(subject="数学", semester="七年级上册", chapter="代数",
                  q_type="choice", content="题 2", answer="B",
                  created_by=teacher_b.id)
    db.add_all([q1, q2])
    db.commit()

    ctx = TenantContext(tenant_id=teacher_a.id, user=teacher_a, source="teacher")
    filtered = tenant_filter(db.query(Question), Question, ctx).all()
    assert len(filtered) == 1
    assert filtered[0].content == "题 1"


def test_tenant_filter_rejects_model_without_created_by():
    class Fake:
        __name__ = "Fake"
    ctx = TenantContext(tenant_id=1, user=None, source="teacher")
    with pytest.raises(ValueError, match="created_by"):
        tenant_filter(None, Fake, ctx)


# ─── Task 5: question_service tenant-aware queries ───

def test_question_service_filters_by_tenant(db, teacher_a, teacher_b):
    db.add_all([
        Question(subject="数学", semester="七年级上册", chapter="代数",
                 q_type="choice", content="A1", answer="A",
                 created_by=teacher_a.id),
        Question(subject="数学", semester="七年级上册", chapter="代数",
                 q_type="choice", content="O1", answer="B",
                 created_by=teacher_b.id),
    ])
    db.commit()

    qs = question_service.get_questions_for_tenant(
        db, tenant_id=teacher_a.id, subject=None, semester=None,
        chapter=None, q_type=None, difficulty=None, bank_id=None,
        limit=20, offset=0,
    )
    assert {q.content for q in qs} == {"A1"}


# ─── Task 6: API list + detail cross-tenant isolation ───

def test_api_list_questions_isolated_between_teachers(db, teacher_a, teacher_b):
    db.add_all([
        Question(subject="数学", semester="七年级上册", chapter="代数",
                 q_type="choice", content="A 的题", answer="A",
                 created_by=teacher_a.id),
        Question(subject="数学", semester="七年级上册", chapter="代数",
                 q_type="choice", content="O 的题", answer="B",
                 created_by=teacher_b.id),
    ])
    db.commit()

    client = TestClient(main_app)
    token_a = create_access_token({"user_id": teacher_a.id})
    r = client.get("/api/v1/questions", headers={"Authorization": f"Bearer {token_a}"})
    assert r.status_code == 200
    contents = [q["content"] for q in r.json()["data"]]
    assert "A 的题" in contents
    assert "O 的题" not in contents


def test_api_get_question_detail_cross_tenant_returns_404(db, teacher_a, teacher_b):
    q = Question(subject="数学", semester="七年级上册", chapter="代数",
                 q_type="choice", content="不应被看见", answer="A",
                 created_by=teacher_b.id)
    db.add(q)
    db.commit()
    db.refresh(q)

    client = TestClient(main_app)
    token_a = create_access_token({"user_id": teacher_a.id})
    r = client.get(f"/api/v1/questions/{q.id}", headers={"Authorization": f"Bearer {token_a}"})
    assert r.status_code == 404


# ─── Task 7: API write ops tenant isolation ───

def test_create_question_assigns_tenant_as_created_by(db, teacher_a):
    client = TestClient(main_app)
    token = create_access_token({"user_id": teacher_a.id})
    r = client.post("/api/v1/questions",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "subject": "数学", "semester": "七年级上册", "chapter": "代数",
            "q_type": "choice", "content": "新题", "answer": "A",
            "difficulty": 1,
        })
    assert r.status_code == 200
    created_id = r.json()["data"]["id"]
    q = db.query(Question).filter(Question.id == created_id).first()
    assert q.created_by == teacher_a.id


def test_update_cross_tenant_question_returns_404(db, teacher_a, teacher_b):
    q = Question(subject="数学", semester="七年级上册", chapter="代数",
                 q_type="choice", content="O 的题", answer="A", created_by=teacher_b.id)
    db.add(q)
    db.commit()
    db.refresh(q)
    client = TestClient(main_app)
    token = create_access_token({"user_id": teacher_a.id})
    r = client.put(f"/api/v1/questions/{q.id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"content": "改的"})
    assert r.status_code == 404


def test_delete_cross_tenant_question_returns_404(db, teacher_a, teacher_b):
    q = Question(subject="数学", semester="七年级上册", chapter="代数",
                 q_type="choice", content="O 的题", answer="A", created_by=teacher_b.id)
    db.add(q)
    db.commit()
    db.refresh(q)
    client = TestClient(main_app)
    token = create_access_token({"user_id": teacher_a.id})
    r = client.delete(f"/api/v1/questions/{q.id}", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 404


# ─── Task 8: random endpoint tenant scoping ───

def test_random_endpoint_is_tenant_scoped(db, teacher_a, teacher_b):
    db.add_all([
        Question(subject="数学", semester="七年级上册", chapter="代数",
                 q_type="choice", content=f"O{i}", answer="A", created_by=teacher_b.id)
        for i in range(5)
    ])
    db.commit()
    client = TestClient(main_app)
    token = create_access_token({"user_id": teacher_a.id})
    r = client.get("/api/v1/questions/random?count=10",
                   headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["data"] == []  # teacher_a 名下无题
