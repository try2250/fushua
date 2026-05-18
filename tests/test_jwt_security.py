import pytest
from datetime import timedelta
from app.core.security import create_access_token, verify_token, hash_password, verify_password


def test_create_and_verify_token():
    payload = {"user_id": 123, "role": "student"}
    token = create_access_token(payload)

    assert token is not None
    assert isinstance(token, str)

    decoded = verify_token(token)
    assert decoded["user_id"] == 123
    assert decoded["role"] == "student"


def test_expired_token():
    payload = {"user_id": 123}
    token = create_access_token(payload, expires_delta=timedelta(seconds=-1))

    decoded = verify_token(token)
    assert decoded is None


def test_invalid_token():
    decoded = verify_token("invalid.token.here")
    assert decoded is None


def test_hash_and_verify_password():
    password = "test123456"
    hashed = hash_password(password)

    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("wrong_password", hashed) is False
