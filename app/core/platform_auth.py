"""平台管理员独立认证体系。

故意不与 User token 混用：
- 用不同的 token claim `platform_admin_id`（不是 `user_id`）
- 解析时检查 claim 类型，user token 会被识别为非平台 token
"""
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
import jwt

from app.database import get_db
from app.models import PlatformAdmin
from app.core.config import settings


PLATFORM_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24h


def create_platform_token(pa: PlatformAdmin) -> str:
    payload = {
        "platform_admin_id": pa.id,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=PLATFORM_TOKEN_EXPIRE_MINUTES),
        "kind": "platform_admin",
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def _verify_platform_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except jwt.PyJWTError:
        return None
    if payload.get("kind") != "platform_admin":
        return None
    return payload


def get_current_platform_admin(
    request: Request,
    db: Session = Depends(get_db),
) -> PlatformAdmin:
    auth = request.headers.get("authorization") or request.headers.get("Authorization")
    if not (auth and auth.lower().startswith("bearer ")):
        raise HTTPException(status_code=401, detail="未认证")
    payload = _verify_platform_token(auth.split(" ", 1)[1])
    if not payload:
        raise HTTPException(status_code=401, detail="非平台管理员 token")
    pa_id = payload.get("platform_admin_id")
    if not pa_id:
        raise HTTPException(status_code=401, detail="token 缺字段")
    pa = db.query(PlatformAdmin).filter(
        PlatformAdmin.id == pa_id,
        PlatformAdmin.is_active == True,
    ).first()
    if not pa:
        raise HTTPException(status_code=401, detail="管理员不存在或已禁用")
    return pa
