"""
多租户基础设施

核心概念：
- TenantContext：封装当前请求的租户上下文（tenant_id = 老师 user.id）
- get_tenant_context：FastAPI 依赖，从请求中解析租户身份
- tenant_filter：SQLAlchemy 查询辅助，按 created_by 过滤
"""
from dataclasses import dataclass
from typing import Optional, Literal

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.core.security import verify_token

TenantSource = Literal["teacher", "student", "platform_admin"]


@dataclass
class TenantContext:
    tenant_id: int
    user: Optional[User]
    source: TenantSource

    def __repr__(self) -> str:
        user_id = self.user.id if self.user is not None else None
        return f"TenantContext(tenant_id={self.tenant_id}, source={self.source}, user_id={user_id})"


def _resolve_user_from_request(request: Request, db: Session) -> Optional[User]:
    auth = request.headers.get("authorization") or request.headers.get("Authorization")
    if auth and auth.lower().startswith("bearer "):
        token = auth.split(" ", 1)[1]
        payload = verify_token(token)
        if payload:
            user_id = payload.get("user_id")
            if user_id:
                return db.query(User).filter(User.id == user_id).first()
    session = getattr(request, "session", None)
    if session:
        user_id = session.get("user_id")
        if user_id:
            return db.query(User).filter(User.id == user_id).first()
    return None


def get_tenant_context(
    request: Request,
    db: Session = Depends(get_db),
) -> TenantContext:
    user = _resolve_user_from_request(request, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="未认证")

    if user.role == "teacher":
        return TenantContext(tenant_id=user.id, user=user, source="teacher")

    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="租户解析未实现")
