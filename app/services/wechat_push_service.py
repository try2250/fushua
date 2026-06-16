"""微信订阅消息推送服务。access_token 缓存 2h。"""
import os
import time
import logging
import httpx

logger = logging.getLogger("fushua.wechat")


class WechatPushService:
    def __init__(self):
        self._access_token = None
        self._token_expires_at = 0

    def _get_access_token(self) -> str:
        if self._access_token and time.time() < self._token_expires_at - 60:
            return self._access_token
        appid = os.environ.get("WECHAT_APPID", "")
        secret = os.environ.get("WECHAT_SECRET", "")
        if not appid or not secret:
            return "no_credentials"
        try:
            resp = httpx.get(
                "https://api.weixin.qq.com/cgi-bin/token",
                params={"grant_type": "client_credential", "appid": appid, "secret": secret},
                timeout=10,
            )
            data = resp.json()
            self._access_token = data.get("access_token", "")
            self._token_expires_at = time.time() + data.get("expires_in", 7200)
            return self._access_token
        except Exception as e:
            logger.warning(f"Failed to get access_token: {e}")
            return ""

    def send_subscribe_message(self, openid: str, template_id: str, data: dict, page: str = "") -> dict:
        access_token = self._get_access_token()
        if not access_token or access_token == "no_credentials":
            return {"errcode": -1, "errmsg": "no credentials"}
        try:
            resp = httpx.post(
                f"https://api.weixin.qq.com/cgi-bin/message/subscribe/send?access_token={access_token}",
                json={"touser": openid, "template_id": template_id, "data": data, "page": page},
                timeout=10,
            )
            return resp.json()
        except Exception as e:
            logger.warning(f"Wechat push failed: {e}")
            return {"errcode": -1, "errmsg": str(e)}


wechat_push_service = WechatPushService()
