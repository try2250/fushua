"""Plan 1.2B — PlatformAdmin 模型测试"""
import pytest
from app.models import PlatformAdmin


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
