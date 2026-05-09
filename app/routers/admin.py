from datetime import datetime
from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from typing import Annotated

from app.database import get_db
from app.models import User, ClassGroup, Question, ClassMember, AuditLog
from app.auth import get_current_user
from app.security import validate_csrf_async

router = APIRouter()


def require_admin(request: Request, db: Session):
    user_id = get_current_user(request)
    if not user_id:
        raise HTTPException(status_code=303, headers={"Location": "/login"})
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_admin:
        raise HTTPException(status_code=403)
    return user


@router.get("/admin")
def admin_index(request: Request, db: Annotated[Session, Depends(get_db)]):
    require_admin(request, db)
    user_count = db.query(User).count()
    class_count = db.query(ClassGroup).count()
    question_count = db.query(Question).count()
    teacher_count = db.query(User).filter(User.role == "teacher").count()
    guest_count = db.query(User).filter(User.is_guest == True).count()
    return request.app.state.templates.TemplateResponse(
        "admin/index.html",
        {
            "request": request,
            "user_count": user_count,
            "class_count": class_count,
            "question_count": question_count,
            "teacher_count": teacher_count,
            "guest_count": guest_count,
        },
    )


@router.get("/admin/users")
def admin_users(request: Request, db: Annotated[Session, Depends(get_db)], q: str = "", role: str = ""):
    require_admin(request, db)
    query = db.query(User)
    if q:
        query = query.filter(
            (User.username.contains(q)) | (User.display_name.contains(q))
        )
    if role:
        query = query.filter(User.role == role)
    users = query.order_by(User.created_at.desc()).all()
    return request.app.state.templates.TemplateResponse(
        "admin/users.html",
        {"request": request, "users": users, "q": q, "role": role},
    )


@router.post("/admin/users/{user_id}/reset-password")
async def reset_password(user_id: int, request: Request, db: Annotated[Session, Depends(get_db)]):
    admin_user = require_admin(request, db)
    await validate_csrf_async(request)
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    user.password_hash = User.hash_password("abc123")
    db.add(AuditLog(
        actor_id=admin_user.id,
        action="reset_password",
        target_type="user",
        target_id=user_id,
        detail=f"管理员重置用户 {user.username} 的密码"
    ))
    db.commit()
    return RedirectResponse(url="/admin/users", status_code=303)


@router.post("/admin/users/{user_id}/toggle-disable")
async def toggle_disable(user_id: int, request: Request, db: Annotated[Session, Depends(get_db)]):
    admin_user = require_admin(request, db)
    await validate_csrf_async(request)
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    if user.is_admin:
        raise HTTPException(status_code=403, detail="不能禁用管理员账号")
    user.is_disabled = not user.is_disabled
    db.add(AuditLog(
        actor_id=admin_user.id,
        action="toggle_disable",
        target_type="user",
        target_id=user_id,
        detail=f"{'禁用' if user.is_disabled else '启用'}用户 {user.username}"
    ))
    db.commit()
    return RedirectResponse(url="/admin/users", status_code=303)


@router.post("/admin/cleanup-guests")
async def cleanup_guests(request: Request, db: Annotated[Session, Depends(get_db)]):
    admin_user = require_admin(request, db)
    await validate_csrf_async(request)
    now = datetime.now()
    expired_guests = db.query(User).filter(
        User.is_guest == True,
        User.guest_expires_at != None,
        User.guest_expires_at < now,
    ).all()
    count = len(expired_guests)
    for guest in expired_guests:
        db.query(ClassMember).filter(ClassMember.user_id == guest.id).delete()
        db.delete(guest)
    db.add(AuditLog(
        actor_id=admin_user.id,
        action="cleanup_guests",
        target_type="system",
        detail=f"清理了 {count} 个过期游客"
    ))
    db.commit()
    return RedirectResponse(url="/admin", status_code=303)
