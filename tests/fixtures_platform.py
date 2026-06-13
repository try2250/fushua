"""Plan 1.2B — PlatformAdmin fixture"""
import pytest
from app.models import PlatformAdmin
from app.core.platform_auth import create_platform_token


@pytest.fixture
def platform_admin(db):
    pa = PlatformAdmin(
        username="root",
        password_hash=PlatformAdmin.hash_password("rootpass"),
        email="root@fushua.local",
    )
    db.add(pa); db.commit(); db.refresh(pa)
    return pa


@pytest.fixture
def platform_admin_token(platform_admin):
    return create_platform_token(platform_admin)
