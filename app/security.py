import time
from datetime import datetime, timedelta
from fastapi import Request, HTTPException


def sanitize_input(value: str, max_length: int = 500) -> str:
    if not value:
        return value
    value = value.strip()
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
    if len(password) < 6:
        return "密码长度至少6位"
    if password.isdigit():
        return "密码不能为纯数字"
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


def verify_teacher_invite_code(code: str, db) -> bool:
    from app.models import SiteConfig
    if not code:
        return False
    config = db.query(SiteConfig).filter(SiteConfig.key == "teacher_invite_code").first()
    if not config or not config.value:
        return False
    codes = [c.strip() for c in config.value.split(",") if c.strip()]
    return code in codes
