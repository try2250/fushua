"""小程序错误上报测试"""
from fastapi.testclient import TestClient
from app.main import app as main_app


def test_client_error_accepts_minimal_payload():
    client = TestClient(main_app)
    r = client.post("/api/v1/client-error", json={
        "message": "TypeError: undefined is not a function",
        "page": "pages/practice/practice",
        "platform": "wechat-miniprogram",
        "ts": 1718244000,
    })
    assert r.status_code == 200
    body = r.json()
    assert body["data"]["received"] is True


def test_client_error_validates_required_message():
    client = TestClient(main_app)
    r = client.post("/api/v1/client-error", json={"page": "x"})
    assert r.status_code == 422


def test_client_error_rejects_huge_payload():
    client = TestClient(main_app)
    huge = "x" * 200_000
    r = client.post("/api/v1/client-error", json={"message": "boom", "stack": huge})
    assert r.status_code == 422
