from fastapi import Request, HTTPException, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User


def get_current_user(request: Request, db: Session = None):
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    if db:
        user = db.query(User).filter(User.id == user_id).first()
        if not user or user.is_disabled:
            request.session.clear()
            return None
    return user_id


def get_current_user_info(request: Request, db: Session = None):
    user_id = request.session.get("user_id")
    if not user_id or not db:
        return None, None, ""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return None, None, ""
    return user, user.role, user.display_name


def require_login(request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user(request, db)
    if not user_id:
        raise HTTPException(status_code=303, headers={"Location": "/login"})
    return user_id


def require_teacher(request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user(request, db)
    if not user_id:
        raise HTTPException(status_code=303, headers={"Location": "/login"})
    user = db.query(User).filter(User.id == user_id).first()
    if not user or (user.role != "teacher" and user.role != "admin"):
        raise HTTPException(status_code=403, detail="仅教师可访问")
    return user_id


from datetime import datetime

def is_guest_expired(user) -> bool:
    if not user.is_guest:
        return False
    if not user.guest_expires_at:
        return True
    return datetime.now() > user.guest_expires_at


def require_non_guest(request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user(request, db)
    if not user_id:
        raise HTTPException(status_code=303, headers={"Location": "/login"})
    user = db.query(User).filter(User.id == user_id).first()
    if user and user.is_guest and is_guest_expired(user):
        raise HTTPException(status_code=303, headers={"Location": "/student/guest-expired"})
    return user_id


def require_admin_role(request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user(request, db)
    if not user_id:
        raise HTTPException(status_code=303, headers={"Location": "/login"})
    user = db.query(User).filter(User.id == user_id).first()
    if not user or user.role != "admin":
        raise HTTPException(status_code=403, detail="仅管理员可访问")
    return user_id
