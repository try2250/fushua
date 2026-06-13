import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from app.models import User, ClassGroup, ClassMember
from sqlalchemy.orm import Session
from tests.conftest import login_as, get_csrf_token


def _platform_login(client, platform_admin):
    from tests.conftest import get_csrf_token
    csrf = get_csrf_token(client)
    return client.post("/platform/login", data={
        "username": platform_admin.username, "password": "rootpass", "_csrf_token": csrf,
    }, follow_redirects=False)


def test_admin_can_preview_test_accounts(client: TestClient, db: Session, platform_admin):
    pytest.skip("batch-cleanup route removed in Plan 1.2B")


def test_admin_can_cleanup_test_accounts(client: TestClient, db: Session, platform_admin):
    pytest.skip("batch-cleanup route removed in Plan 1.2B")


def test_admin_can_preview_expired_guests(client: TestClient, db: Session, platform_admin):
    pytest.skip("batch-cleanup route removed in Plan 1.2B")


def test_admin_can_preview_invalid_data(client: TestClient, db: Session, platform_admin):
    pytest.skip("batch-cleanup route removed in Plan 1.2B")
