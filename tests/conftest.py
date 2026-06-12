import os
import json
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

os.environ["SECRET_KEY"] = "test-secret-key-for-tdd"

from app.database import Base, get_db
from app.main import app
from app.models import User, Question, Record, FieldConfig, SiteConfig

SQLALCHEMY_DATABASE_URL = "sqlite://"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    with engine.connect() as conn:
        conn.execute(text("PRAGMA foreign_keys=OFF"))
        for table in reversed(Base.metadata.sorted_tables):
            try:
                conn.execute(table.delete())
            except Exception:
                pass
        conn.commit()
    yield
    with engine.connect() as conn:
        conn.execute(text("PRAGMA foreign_keys=OFF"))
        for table in reversed(Base.metadata.sorted_tables):
            try:
                conn.execute(table.delete())
            except Exception:
                pass
        conn.commit()


@pytest.fixture
def client():
    return TestClient(app, follow_redirects=False)


@pytest.fixture
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def db():
    """Alias for db_session to match specification naming"""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_test_user(db, username="testuser", role="student", password="abc12345"):
    user = User(
        username=username,
        password_hash=User.hash_password(password),
        role=role,
        display_name=username,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def create_test_question(db, subject="数学", q_type="choice", created_by=1, **kwargs):
    q = Question(
        subject=subject,
        semester=kwargs.get("semester", "八年级上册"),
        chapter=kwargs.get("chapter", "代数"),
        q_type=q_type,
        difficulty=kwargs.get("difficulty", 2),
        content=kwargs.get("content", "1+1等于几？"),
        option_a=kwargs.get("option_a", "1"),
        option_b=kwargs.get("option_b", "2"),
        option_c=kwargs.get("option_c", "3"),
        option_d=kwargs.get("option_d", "4"),
        answer=kwargs.get("answer", "B"),
        explanation=kwargs.get("explanation", "1+1=2"),
        created_by=created_by,
    )
    db.add(q)
    db.commit()
    db.refresh(q)
    return q


def get_csrf_token(client):
    response = client.get("/login", follow_redirects=True)
    text = response.text
    idx = text.find("_csrf_token")
    if idx < 0:
        return "test-csrf-token"
    val_start = text.find("value=", idx) + 7
    val_end = text.find('"', val_start)
    return text[val_start:val_end]


def login_as(client, username, password="abc12345"):
    csrf = get_csrf_token(client)
    return client.post("/login", data={
        "username": username,
        "password": password,
        "_csrf_token": csrf,
    }, follow_redirects=False)


def register_and_login(client, username="testuser", role="student", password="abc12345"):
    if role == "teacher":
        db = TestingSessionLocal()
        try:
            config = db.query(SiteConfig).filter(SiteConfig.key == "teacher_invite_code").first()
            if not config:
                config = SiteConfig(key="teacher_invite_code", value="FUSHUA2024")
                db.add(config)
            else:
                config.value = "FUSHUA2024"
            db.commit()
        finally:
            db.close()
    if role == "admin":
        db = TestingSessionLocal()
        try:
            config = db.query(SiteConfig).filter(SiteConfig.key == "admin_invite_code").first()
            if not config:
                config = SiteConfig(key="admin_invite_code", value="ADMIN2026")
                db.add(config)
            else:
                config.value = "ADMIN2026"
            db.commit()
        finally:
            db.close()
    csrf = get_csrf_token(client)
    data = {
        "username": username,
        "password": password,
        "role": role,
        "display_name": username,
        "_csrf_token": csrf,
    }
    if role == "teacher":
        data["invite_code"] = "FUSHUA2024"
    if role == "admin":
        data["invite_code"] = "ADMIN2026"
    if role == "student":
        data["join_mode"] = "guest"
    client.post("/register", data=data, follow_redirects=True)
    return login_as(client, username, password)


# ─── Multi-tenant fixtures (Plan 1.1) ───
from tests.fixtures_tenant import (  # noqa: E402, F401
    teacher_a, teacher_b, teacher_a_token, teacher_b_token, class_b_with_student
)
