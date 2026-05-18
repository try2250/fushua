import httpx
from typing import Optional, Dict
from app.core.config import settings


class WechatService:

    WECHAT_API_BASE = "https://api.weixin.qq.com"

    def get_openid(self, code: str) -> Optional[Dict[str, str]]:
        url = f"{self.WECHAT_API_BASE}/sns/jscode2session"
        params = {
            "appid": settings.WECHAT_APP_ID,
            "secret": settings.WECHAT_APP_SECRET,
            "js_code": code,
            "grant_type": "authorization_code"
        }

        try:
            response = httpx.get(url, params=params, timeout=10.0)
            data = response.json()

            if "errcode" in data:
                return None

            return {
                "openid": data.get("openid"),
                "session_key": data.get("session_key")
            }
        except Exception:
            return None

    def decrypt_phone_number(self, encrypted_data: str, iv: str, session_key: str) -> Optional[str]:
        pass


wechat_service = WechatService()
