"""Plan 4.1 — WechatPushService 单测（mock 微信 API）"""
import pytest
from unittest.mock import patch, MagicMock
from app.services.wechat_push_service import WechatPushService


def test_get_access_token_cached(monkeypatch):
    """access_token 同一次初始化内不重复请求"""
    monkeypatch.setenv("WECHAT_APPID", "wx_test_appid")
    monkeypatch.setenv("WECHAT_SECRET", "test_secret")

    svc = WechatPushService()
    fake_resp = MagicMock()
    fake_resp.json.return_value = {"access_token": "token_abc", "expires_in": 7200}

    call_count = 0
    def fake_get(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        return fake_resp

    with patch("app.services.wechat_push_service.httpx.get", side_effect=fake_get):
        t1 = svc._get_access_token()
        t2 = svc._get_access_token()
        assert t1 == "token_abc"
        assert t2 == "token_abc"
        assert call_count == 1  # cached


def test_send_subscribe_message_mock():
    """send_subscribe_message 调微信 API 并返回结果"""
    svc = WechatPushService()
    svc._access_token = "mock_token"
    svc._token_expires_at = 9999999999

    fake_resp = MagicMock()
    fake_resp.json.return_value = {"errcode": 0, "errmsg": "ok"}

    with patch("app.services.wechat_push_service.httpx.post", return_value=fake_resp) as mock_post:
        result = svc.send_subscribe_message("o_user123", "tmpl_abc", {"thing1": {"value": "hello"}}, "pages/index/index")
        assert result["errcode"] == 0
        mock_post.assert_called_once()


def test_send_subscribe_message_handles_failure():
    """微信返回错误时不应抛异常"""
    svc = WechatPushService()
    svc._access_token = "bad_token"
    svc._token_expires_at = 9999999999

    fake_resp = MagicMock()
    fake_resp.json.return_value = {"errcode": 40001, "errmsg": "invalid credential"}

    with patch("httpx.post", return_value=fake_resp):
        result = svc.send_subscribe_message("o_x", "t_x", {}, "")
        assert result["errcode"] == 40001  # returns error dict, not exception
