import pytest
from unittest.mock import patch, MagicMock
from app.services.wechat_service import WechatService


@pytest.fixture
def wechat_service():
    return WechatService()


@patch('httpx.get')
def test_get_openid_success(mock_get, wechat_service):
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "openid": "test_openid",
        "session_key": "test_session_key"
    }
    mock_get.return_value = mock_response

    result = wechat_service.get_openid("test_code")

    assert result["openid"] == "test_openid"
    assert result["session_key"] == "test_session_key"


@patch('httpx.get')
def test_get_openid_failure(mock_get, wechat_service):
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "errcode": 40029,
        "errmsg": "invalid code"
    }
    mock_get.return_value = mock_response

    result = wechat_service.get_openid("invalid_code")

    assert result is None


@patch('httpx.get')
def test_get_openid_network_error(mock_get, wechat_service):
    mock_get.side_effect = Exception("Network error")

    result = wechat_service.get_openid("test_code")

    assert result is None
