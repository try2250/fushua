"""E2E 测试共享 fixture。"""
import pytest
from fastapi.testclient import TestClient
from app.main import app as main_app
from app.models import User, ClassGroup, ClassMember, PlatformAdmin
from app.services.email_service import email_service
from tests.conftest import TestingSessionLocal


@pytest.fixture
def client():
    return TestClient(main_app, follow_redirects=False)


@pytest.fixture
def db():
    s = TestingSessionLocal()
    try:
        yield s
    finally:
        s.close()


def _csrf(client) -> str:
    r = client.get("/login", follow_redirects=True)
    txt = r.text
    idx = txt.find("_csrf_token")
    if idx < 0:
        return "test-csrf-token"
    val_start = txt.find("value=", idx) + 7
    val_end = txt.find('"', val_start)
    return txt[val_start:val_end]


@pytest.fixture
def register_teacher(db, client):
    def _do(email_suffix: str = "1"):
        email = f"e2e_teacher_{email_suffix}@school.cn"
        r = client.post("/api/v1/auth/email/send-code", json={
            "email": email, "purpose": "register",
        })
        assert r.status_code == 200
        code = email_service.generate_code(db, email, "register")
        r = client.post("/api/v1/auth/register-teacher", json={
            "email": email,
            "password": "teacher123",
            "display_name": f"E2E 老师 {email_suffix}",
            "code": code,
        })
        assert r.status_code == 200, r.text
        token = r.json()["data"]["token"]
        return email, token
    return _do


@pytest.fixture
def platform_admin_logged_in(db, client):
    pa = db.query(PlatformAdmin).filter(PlatformAdmin.username == "e2e_root").first()
    if not pa:
        pa = PlatformAdmin(username="e2e_root", password_hash=PlatformAdmin.hash_password("e2e_rootpass"), email="e2e_root@fushua.local")
        db.add(pa); db.commit()
    csrf = _csrf(client)
    r = client.post("/platform/login", data={"username": "e2e_root", "password": "e2e_rootpass", "_csrf_token": csrf}, follow_redirects=False)
    assert r.status_code == 303
    return client


@pytest.fixture
def student_in_class(db, client):
    from app.core.security import create_access_token
    def _do(teacher_id: int, class_name: str = "E2E 班"):
        cls = ClassGroup(name=class_name, created_by=teacher_id)
        db.add(cls); db.commit(); db.refresh(cls)
        student = User(username=f"e2e_stu_{teacher_id}_{class_name}", password_hash=User.hash_password("student123"), role="student", display_name="E2E 学生")
        db.add(student); db.commit(); db.refresh(student)
        db.add(ClassMember(class_id=cls.id, user_id=student.id))
        db.commit()
        token = create_access_token({"user_id": student.id})
        return student, cls, token
    return _do
