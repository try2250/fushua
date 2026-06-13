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


@pytest.mark.skip(reason="Admin role removed (Plan 1.2B)")
def test_default_admin_has_force_password_change(db_session):
    pass
