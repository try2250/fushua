"""邮箱验证码服务。

存储复用 SiteConfig，key 前缀区分：
- email_code:<purpose>:<email>      → 验证码内容
- email_limit:<purpose>:<email>    → 限流计数
"""
import json
import random
import time

from sqlalchemy.orm import Session
from app.models import SiteConfig


MAX_PER_HOUR = 5
WINDOW_SECONDS = 3600
CODE_TTL_SECONDS = 600


class EmailServiceError(Exception):
    pass


class EmailService:
    def _key_code(self, purpose: str, email: str) -> str:
        return f"email_code:{purpose}:{email.lower()}"

    def _key_limit(self, purpose: str, email: str) -> str:
        return f"email_limit:{purpose}:{email.lower()}"

    def _check_rate_limit(self, db: Session, purpose: str, email: str) -> None:
        key = self._key_limit(purpose, email)
        row = db.query(SiteConfig).filter(SiteConfig.key == key).first()
        now = int(time.time())
        attempts = json.loads(row.value) if row and row.value else []
        attempts = [t for t in attempts if now - t < WINDOW_SECONDS]
        if len(attempts) >= MAX_PER_HOUR:
            raise EmailServiceError(f"邮箱验证码请求过于频繁，请稍后再试（每小时上限 {MAX_PER_HOUR}）")
        attempts.append(now)
        if row:
            row.value = json.dumps(attempts)
        else:
            db.add(SiteConfig(key=key, value=json.dumps(attempts)))
        db.commit()

    def generate_code(self, db: Session, email: str, purpose: str = "register") -> str:
        self._check_rate_limit(db, purpose, email)
        code = f"{random.randint(0, 999999):06d}"
        payload = json.dumps({"code": code, "ts": int(time.time())})
        key = self._key_code(purpose, email)
        row = db.query(SiteConfig).filter(SiteConfig.key == key).first()
        if row:
            row.value = payload
        else:
            db.add(SiteConfig(key=key, value=payload))
        db.commit()
        self._deliver(email, code, purpose)
        return code

    def verify_code(self, db: Session, email: str, code: str, purpose: str = "register") -> bool:
        key = self._key_code(purpose, email)
        row = db.query(SiteConfig).filter(SiteConfig.key == key).first()
        if not row or not row.value:
            return False
        try:
            data = json.loads(row.value)
        except (ValueError, TypeError):
            return False
        if int(time.time()) - data["ts"] > CODE_TTL_SECONDS:
            return False
        if data["code"] != code:
            return False
        row.value = ""
        db.commit()
        return True

    def _deliver(self, email: str, code: str, purpose: str) -> None:
        import logging
        logging.getLogger("fushua.email").info(
            "[DEV] 验证码 to=%s purpose=%s code=%s", email, purpose, code
        )


email_service = EmailService()
