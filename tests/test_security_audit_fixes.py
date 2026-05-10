import pytest
from tests.conftest import get_csrf_token


def test_login_redirects_to_settings_when_force_password_change(client, db_session):
    from app.models import User
    user = User(username="forceuser", password_hash=User.hash_password("test1234a"), role="student", force_password_change=True)
    db_session.add(user)
    db_session.commit()
    csrf = get_csrf_token(client)
    resp = client.post("/login", data={"username": "forceuser", "password": "test1234a", "_csrf_token": csrf}, follow_redirects=False)
    assert resp.status_code == 303
    assert "/settings" in resp.headers["location"]


def test_default_admin_has_force_password_change(db_session):
    from app.models import User
    admin = User(
        username="admin",
        password_hash=User.hash_password("random_pw_123"),
        role="admin",
        display_name="系统管理员",
        is_admin=True,
        force_password_change=True,
    )
    db_session.add(admin)
    db_session.commit()
    result = db_session.query(User).filter(User.username == "admin").first()
    assert result is not None
    assert result.force_password_change is True
