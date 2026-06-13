"""平台批量清理：过期游客、空班级等。"""
from datetime import datetime
from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, ClassGroup, ClassMember, PlatformAdmin
from app.routers.platform_users import _require_platform


router = APIRouter(prefix="/platform")


@router.get("/batch-cleanup")
def batch_cleanup_page(request: Request, db: Session = Depends(get_db), pa: PlatformAdmin = Depends(_require_platform)):
    now = datetime.utcnow()
    expired_guests = db.query(User).filter(User.is_guest == True, User.guest_expires_at != None, User.guest_expires_at < now).count()
    empty_classes = 0
    for cls in db.query(ClassGroup).all():
        cnt = db.query(ClassMember).filter(ClassMember.class_id == cls.id).count()
        if cnt == 0:
            empty_classes += 1
    return request.app.state.templates.TemplateResponse("platform/batch_cleanup.html", {"request": request, "pa": pa, "expired_guests": expired_guests, "empty_classes": empty_classes})


@router.post("/batch-cleanup")
def batch_cleanup_action(request: Request, target: str = Form(...), db: Session = Depends(get_db), pa: PlatformAdmin = Depends(_require_platform)):
    now = datetime.utcnow()
    if target == "expired_guests":
        rows = db.query(User).filter(User.is_guest == True, User.guest_expires_at != None, User.guest_expires_at < now).all()
        for u in rows:
            db.query(ClassMember).filter(ClassMember.user_id == u.id).delete()
            db.delete(u)
        db.commit()
    elif target == "empty_classes":
        for cls in db.query(ClassGroup).all():
            cnt = db.query(ClassMember).filter(ClassMember.class_id == cls.id).count()
            if cnt == 0:
                db.delete(cls)
        db.commit()
    return RedirectResponse(url="/platform/batch-cleanup", status_code=303)
