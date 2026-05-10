import time
import html
import re
from datetime import datetime, timedelta
from fastapi import Request, HTTPException


def sanitize_input(value: str, max_length: int = 500) -> str:
    if not value:
        return value
    value = value.strip()
    value = html.escape(value)
    value = re.sub(r'javascript:', '', value, flags=re.IGNORECASE)
    value = re.sub(r'on\w+\s*=', '', value, flags=re.IGNORECASE)
    if len(value) > max_length:
        value = value[:max_length]
    return value


LOGIN_MAX_ATTEMPTS = 5
LOGIN_LOCKOUT_SECONDS = 300


def check_login_rate_limit(username: str, db=None) -> None:
    if not db:
        return
    from app.models import SiteConfig
    attempts_key = f"_login_fail:{username.lower()}"
    config = db.query(SiteConfig).filter(SiteConfig.key == attempts_key).first()
    if config:
        try:
            entries = [float(t) for t in config.value.split(",") if t.strip()]
            now = time.time()
            entries = [t for t in entries if now - t < LOGIN_LOCKOUT_SECONDS]
            if len(entries) >= LOGIN_MAX_ATTEMPTS:
                raise HTTPException(
                    status_code=429,
                    detail=f"登录失败次数过多，请{LOGIN_LOCKOUT_SECONDS}秒后重试"
                )
            config.value = ",".join(str(t) for t in entries)
        except ValueError:
            config.value = ""


def record_login_attempt(username: str, db=None) -> None:
    if not db:
        return
    from app.models import SiteConfig
    attempts_key = f"_login_fail:{username.lower()}"
    config = db.query(SiteConfig).filter(SiteConfig.key == attempts_key).first()
    now = str(time.time())
    if config:
        try:
            entries = [float(t) for t in config.value.split(",") if t.strip()]
            cutoff = time.time() - LOGIN_LOCKOUT_SECONDS
            entries = [t for t in entries if t > cutoff]
            entries.append(time.time())
            config.value = ",".join(str(t) for t in entries)
        except ValueError:
            config.value = now
    else:
        config = SiteConfig(key=attempts_key, value=now)
        db.add(config)
    db.commit()


def validate_password_strength(password: str) -> str | None:
    if len(password) < 8:
        return "密码长度至少8位"
    if password.isdigit():
        return "密码不能为纯数字"
    if password.isalpha():
        return "密码不能为纯字母"
    return None


async def validate_csrf_async(request: Request) -> None:
    token = request.session.get("csrf_token", "")
    if not token:
        raise HTTPException(status_code=403, detail="缺少 CSRF token")
    if request.method not in ("POST", "PUT", "DELETE", "PATCH"):
        return
    form = await request.form()
    form_token = form.get("_csrf_token", "")
    if not form_token or form_token != token:
        raise HTTPException(status_code=403, detail="CSRF 校验失败")


def verify_invite_code(code: str, db, key: str) -> bool:
    from app.models import SiteConfig
    if not code:
        return False
    config = db.query(SiteConfig).filter(SiteConfig.key == key).first()
    if not config or not config.value:
        return False
    codes = [c.strip() for c in config.value.split(",") if c.strip()]
    return code in codes


def verify_teacher_invite_code(code: str, db) -> bool:
    return verify_invite_code(code, db, "teacher_invite_code")


def verify_admin_invite_code(code: str, db) -> bool:
    return verify_invite_code(code, db, "admin_invite_code")


REGISTER_MAX_ATTEMPTS = 5
REGISTER_LOCKOUT_SECONDS = 3600
RECOVER_MAX_ATTEMPTS = 3
RECOVER_LOCKOUT_SECONDS = 3600


def check_rate_limit(key: str, max_attempts: int, lockout_seconds: int, db=None) -> None:
    if not db:
        return
    from app.models import SiteConfig
    config = db.query(SiteConfig).filter(SiteConfig.key == key).first()
    if config:
        try:
            entries = [float(t) for t in config.value.split(",") if t.strip()]
            now = time.time()
            entries = [t for t in entries if now - t < lockout_seconds]
            if len(entries) >= max_attempts:
                raise HTTPException(
                    status_code=429,
                    detail=f"操作过于频繁，请{lockout_seconds}秒后重试"
                )
            config.value = ",".join(str(t) for t in entries)
        except ValueError:
            config.value = ""


def record_rate_limit_attempt(key: str, db=None) -> None:
    if not db:
        return
    from app.models import SiteConfig
    now_str = str(time.time())
    config = db.query(SiteConfig).filter(SiteConfig.key == key).first()
    if config:
        try:
            entries = [float(t) for t in config.value.split(",") if t.strip()]
            cutoff = time.time() - 3600
            entries = [t for t in entries if t > cutoff]
            entries.append(time.time())
            config.value = ",".join(str(t) for t in entries)
        except ValueError:
            config.value = now_str
    else:
        config = SiteConfig(key=key, value=now_str)
        db.add(config)
    db.flush()
