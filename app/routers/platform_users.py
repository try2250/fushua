"""平台用户管理。"""
from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.database import get_db, SessionLocal
from app.models import User, PlatformAdmin


router = APIRouter(prefix="/platform")


def _require_platform(request: Request, db: Session = Depends(get_db)) -> PlatformAdmin:
    pa_id = request.session.get("platform_admin_id")
    if not pa_id:
        raise HTTPException(status_code=303, headers={"location": "/platform/login"})
    pa = db.query(PlatformAdmin).filter(
        PlatformAdmin.id == pa_id, PlatformAdmin.is_active == True,
    ).first()
    if not pa:
        raise HTTPException(status_code=303, headers={"location": "/platform/login"})
    return pa


@router.get("/users")
def list_users(
    request: Request,
    q: str = "",
    role: str = "",
    db: Session = Depends(get_db),
    pa: PlatformAdmin = Depends(_require_platform),
):
    query = db.query(User)
    if q:
        like = f"%{q}%"
        query = query.filter(or_(User.username.ilike(like), User.display_name.ilike(like)))
    if role:
        query = query.filter(User.role == role)
    users = query.order_by(User.created_at.desc()).limit(100).all()
    return request.app.state.templates.TemplateResponse(
        "platform/users.html",
        {"request": request, "pa": pa, "users": users, "q": q, "role": role},
    )


@router.get("/users/{user_id}")
def user_detail(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    pa: PlatformAdmin = Depends(_require_platform),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return request.app.state.templates.TemplateResponse(
        "platform/user_detail.html",
        {"request": request, "pa": pa, "user": user},
    )


@router.post("/users/{user_id}/reset-password")
def reset_password(
    user_id: int,
    db: Session = Depends(get_db),
    pa: PlatformAdmin = Depends(_require_platform),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    user.password_hash = User.hash_password("abc12345")
    user.force_password_change = True
    db.commit()
    return RedirectResponse(url=f"/platform/users/{user_id}", status_code=303)


@router.post("/users/{user_id}/toggle-disable")
def toggle_disable(
    user_id: int,
    db: Session = Depends(get_db),
    pa: PlatformAdmin = Depends(_require_platform),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    user.is_disabled = not user.is_disabled
    db.commit()
    return RedirectResponse(url=f"/platform/users/{user_id}", status_code=303)


@router.post("/users/{user_id}/delete")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    pa: PlatformAdmin = Depends(_require_platform),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    db.delete(user); db.commit()
    return RedirectResponse(url="/platform/users", status_code=303)
