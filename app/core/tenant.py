"""
多租户基础设施

核心概念：
- TenantContext：封装当前请求的租户上下文（tenant_id = 老师 user.id）
- get_tenant_context：FastAPI 依赖，从请求中解析租户身份
- tenant_filter：SQLAlchemy 查询辅助，按 created_by 过滤
"""
import structlog
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
        structlog.contextvars.bind_contextvars(tenant_id=user.id, tenant_source="teacher")
        return TenantContext(tenant_id=user.id, user=user, source="teacher")

    if user.role == "student":
        class_id_str = request.query_params.get("class_id")
        if not class_id_str:
            raise HTTPException(status_code=400, detail="缺少 class_id 参数")
        try:
            class_id = int(class_id_str)
        except ValueError:
            raise HTTPException(status_code=400, detail="class_id 必须是整数")

        from app.models import ClassGroup, ClassMember  # 局部 import 避免循环

        member = db.query(ClassMember).filter(
            ClassMember.class_id == class_id,
            ClassMember.user_id == user.id,
        ).first()
        if not member:
            raise HTTPException(status_code=403, detail="非该班级成员")

        cls = db.query(ClassGroup).filter(ClassGroup.id == class_id).first()
        if not cls:
            raise HTTPException(status_code=404, detail="班级不存在")

        structlog.contextvars.bind_contextvars(tenant_id=cls.created_by, tenant_source="student")
        return TenantContext(tenant_id=cls.created_by, user=user, source="student")

    raise HTTPException(status_code=400, detail=f"未支持的角色: {user.role}")


def tenant_filter(query, model_class, tenant: TenantContext):
    """对 SQLAlchemy Query 应用 tenant 过滤。要求 model 有 created_by 字段。"""
    if not hasattr(model_class, "created_by"):
        raise ValueError(
            f"{model_class.__name__} 没有 created_by 字段，不是租户范围资源"
        )
    return query.filter(model_class.created_by == tenant.tenant_id)
