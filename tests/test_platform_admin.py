"""Plan 1.2B — PlatformAdmin 模型 + 独立认证测试"""
import pytest
from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient
from app.models import PlatformAdmin
from app.database import get_db
from app.core.platform_auth import (
    create_platform_token, get_current_platform_admin,
)
from tests.conftest import TestingSessionLocal


def test_platform_admin_model_basic(db):
    pa = PlatformAdmin(
        username="root",
        password_hash=PlatformAdmin.hash_password("secret123"),
        email="root@fushua.local",
    )
    db.add(pa); db.commit(); db.refresh(pa)
    assert pa.id is not None
    assert pa.username == "root"
    assert PlatformAdmin.verify_password(pa.password_hash, "secret123") is True
    assert PlatformAdmin.verify_password(pa.password_hash, "wrong") is False


# ─── Task 2: PlatformAdmin token ───


def _yield_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def _make_probe_app():
    app = FastAPI()

    @app.get("/p")
    def p(pa=Depends(get_current_platform_admin)):
        return {"id": pa.id, "username": pa.username}

    app.dependency_overrides[get_db] = _yield_session
    return app


def test_platform_token_round_trip(db):
    pa = PlatformAdmin(
        username="root",
        password_hash=PlatformAdmin.hash_password("x"),
        email="r@x.com",
    )
    db.add(pa); db.commit(); db.refresh(pa)
    token = create_platform_token(pa)
    app = _make_probe_app()
    client = TestClient(app)
    r = client.get("/p", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    body = r.json()
    assert body["id"] == pa.id
    assert body["username"] == "root"


def test_user_token_cannot_access_platform_endpoint(db, teacher_a):
    from app.core.security import create_access_token
    user_token = create_access_token({"user_id": teacher_a.id})
    app = _make_probe_app()
    client = TestClient(app)
    r = client.get("/p", headers={"Authorization": f"Bearer {user_token}"})
    assert r.status_code == 401
