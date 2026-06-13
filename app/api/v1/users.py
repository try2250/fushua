from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
from app.schemas.user import UserResponse, UserUpdateRequest, PasswordChangeRequest
from app.schemas.common import ResponseModel
from app.core.deps import get_current_user
from app.core.security import hash_password, verify_password
from app.services.record_service import record_service
from app.api.v1.compat_helpers import record_to_miniprogram_dict, user_stats_for_miniprogram


router = APIRouter(prefix="/users", tags=["用户"])


@router.get("/me", response_model=ResponseModel[UserResponse])
def get_current_user_info(current_user: User = Depends(get_current_user)):
    return ResponseModel(data=UserResponse.model_validate(current_user))


@router.get("/me/stats", response_model=ResponseModel[dict])
def get_current_user_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return ResponseModel(data=user_stats_for_miniprogram(db, current_user))


@router.put("/me", response_model=ResponseModel[UserResponse])
def update_current_user(
    request: UserUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if request.display_name is not None:
        current_user.display_name = request.display_name

    if request.nickname is not None:
        current_user.nickname = request.nickname

    if request.avatar_url is not None:
        current_user.avatar_url = request.avatar_url

    db.commit()
    db.refresh(current_user)

    return ResponseModel(data=UserResponse.model_validate(current_user))


@router.put("/me/password", response_model=ResponseModel[dict])
def change_password(
    request: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not verify_password(request.old_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="旧密码错误")

    current_user.password_hash = hash_password(request.new_password)
    db.commit()

    return ResponseModel(data={"message": "密码修改成功"})


@router.get("/{user_id}", response_model=ResponseModel[UserResponse])
def get_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权访问")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    return ResponseModel(data=UserResponse.model_validate(user))


@router.get("/{user_id}/stats", response_model=ResponseModel[dict])
def get_user_stats(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if user_id != current_user.id and current_user.role != "teacher":
        raise HTTPException(status_code=403, detail="无权访问")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return ResponseModel(data=user_stats_for_miniprogram(db, user))


@router.get("/{user_id}/mistakes", response_model=ResponseModel[list[dict]])
def get_user_mistakes(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if user_id != current_user.id and current_user.role != "teacher":
        raise HTTPException(status_code=403, detail="无权访问")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    mistakes = record_service.get_mistakes(db, user.id)
    return ResponseModel(data=[record_to_miniprogram_dict(record) for record in mistakes])
