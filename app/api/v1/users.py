"""用户 API — Plan 1.4 tenant-scoped endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.deps import get_current_user
from app.core.tenant import TenantContext, get_tenant_context
from app.schemas.user import UserResponse
from app.schemas.common import ResponseModel
from app.models import User, ClassGroup, ClassMember
from app.services.record_service import record_service
from app.api.v1.compat_helpers import user_stats_for_miniprogram, record_to_miniprogram_dict


router = APIRouter(prefix="/users", tags=["用户"])


def _ensure_target_in_tenant(db: Session, tenant: TenantContext, target_user_id: int) -> User:
    user = db.query(User).filter(User.id == target_user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    if user.id == tenant.tenant_id:
        return user
    if tenant.source == "student" and tenant.user and tenant.user.id == user.id:
        return user
    if tenant.source == "teacher":
        in_class = db.query(ClassMember).join(
            ClassGroup, ClassGroup.id == ClassMember.class_id
        ).filter(
            ClassGroup.created_by == tenant.tenant_id,
            ClassMember.user_id == user.id,
        ).first()
        if in_class:
            return user
    raise HTTPException(status_code=404, detail="用户不存在")


@router.get("/me", response_model=ResponseModel[UserResponse])
def get_me(current_user: User = Depends(get_current_user)):
    return ResponseModel(data=UserResponse.model_validate(current_user))


@router.put("/me/password", response_model=ResponseModel[dict])
def change_password(
    old_password: str = None, new_password: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not User.verify_password(current_user.password_hash, old_password):
        raise HTTPException(status_code=400, detail="原密码错误")
    current_user.password_hash = User.hash_password(new_password)
    current_user.force_password_change = False
    db.commit()
    return ResponseModel(data={"message": "密码修改成功"})


@router.get("/{user_id}", response_model=ResponseModel[UserResponse])
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    tenant: TenantContext = Depends(get_tenant_context),
):
    user = _ensure_target_in_tenant(db, tenant, user_id)
    return ResponseModel(data=UserResponse.model_validate(user))


@router.get("/{user_id}/stats", response_model=ResponseModel[dict])
def get_user_stats(
    user_id: int,
    db: Session = Depends(get_db),
    tenant: TenantContext = Depends(get_tenant_context),
):
    user = _ensure_target_in_tenant(db, tenant, user_id)
    return ResponseModel(data=user_stats_for_miniprogram(db, user))


@router.get("/{user_id}/mistakes", response_model=ResponseModel[list[dict]])
def get_user_mistakes(
    user_id: int,
    db: Session = Depends(get_db),
    tenant: TenantContext = Depends(get_tenant_context),
):
    user = _ensure_target_in_tenant(db, tenant, user_id)
    mistakes = record_service.get_mistakes(db, user.id)
    return ResponseModel(data=[record_to_miniprogram_dict(record) for record in mistakes])
