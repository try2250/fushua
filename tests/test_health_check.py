import pytest

def test_health_check_returns_200(client):
    response = client.get("/health")
    assert response.status_code == 200

def test_health_check_includes_status_field(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data

def test_health_check_includes_db_field(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("ok", "degraded")

def test_health_check_includes_user_count_field(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("ok", "degraded")

def test_health_check_db_is_ok(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
