import pytest
from tests.conftest import create_test_user, login_as
from app.core.security import create_access_token


def test_api_login_success(client, db_session):
    user = create_test_user(db_session, "apiuser", role="student")
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "apiuser", "password": "abc12345"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 0
    assert "token" in data["data"]
    assert data["data"]["user"]["username"] == "apiuser"


def test_api_login_wrong_password(client, db_session):
    create_test_user(db_session, "apiuser2", role="student")
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "apiuser2", "password": "wrongpass"}
    )
    assert response.status_code == 401


def test_api_login_missing_fields(client):
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "test"}
    )
    assert response.status_code == 422


def test_api_get_me_with_valid_token(client, db_session):
    user = create_test_user(db_session, "apime", role="student")
    token = create_access_token({"user_id": user.id, "role": user.role, "username": user.username})
    response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 0
    assert data["data"]["username"] == "apime"


def test_api_get_me_without_auth(client):
    response = client.get("/api/v1/users/me")
    assert response.status_code == 403


def test_api_get_me_with_invalid_token(client):
    response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": "Bearer invalid.token.here"}
    )
    assert response.status_code == 401


def test_api_send_sms(client, db_session):
    response = client.post(
        "/api/v1/auth/sms/send",
        json={"phone": "13800138000", "purpose": "bind"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 0


def test_api_send_sms_invalid_phone(client, db_session):
    response = client.post(
        "/api/v1/auth/sms/send",
        json={"phone": "123", "purpose": "bind"}
    )
    assert response.status_code == 422


def test_api_update_user(client, db_session):
    user = create_test_user(db_session, "apiupdate", role="student")
    token = create_access_token({"user_id": user.id, "role": user.role, "username": user.username})
    response = client.put(
        "/api/v1/users/me",
        json={"display_name": "新名字", "nickname": "小刷"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["display_name"] == "新名字"
    assert data["data"]["nickname"] == "小刷"


def test_api_change_password(client, db_session):
    user = create_test_user(db_session, "apipass", role="student")
    token = create_access_token({"user_id": user.id, "role": user.role, "username": user.username})
    response = client.put(
        "/api/v1/users/me/password",
        json={"old_password": "abc12345", "new_password": "newpass123"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200


def test_api_change_password_wrong_old(client, db_session):
    user = create_test_user(db_session, "apipass2", role="student")
    token = create_access_token({"user_id": user.id, "role": user.role, "username": user.username})
    response = client.put(
        "/api/v1/users/me/password",
        json={"old_password": "wrongpass", "new_password": "newpass123"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 400


def test_api_docs_accessible(client):
    response = client.get("/api/docs")
    assert response.status_code == 200


def test_api_openapi_json_accessible(client):
    response = client.get("/api/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert data["info"]["title"] == "付刷 API"
    assert data["info"]["version"] == "4.0.0"
    assert "/api/v1/auth/login" in data["paths"]
