"""平台班级总览。"""
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import ClassGroup, ClassMember, User, PlatformAdmin
from app.routers.platform_users import _require_platform


router = APIRouter(prefix="/platform")


@router.get("/classes")
def list_classes(
    request: Request,
    db: Session = Depends(get_db),
    pa: PlatformAdmin = Depends(_require_platform),
):
    rows = []
    for c in db.query(ClassGroup).order_by(ClassGroup.created_at.desc()).all():
        creator = db.query(User).filter(User.id == c.created_by).first()
        member_count = db.query(ClassMember).filter(ClassMember.class_id == c.id).count()
        rows.append({
            "id": c.id, "name": c.name,
            "creator": creator.display_name if creator else "?",
            "creator_email": creator.username if creator else "?",
            "member_count": member_count, "created_at": c.created_at,
        })
    return request.app.state.templates.TemplateResponse(
        "platform/classes.html",
        {"request": request, "pa": pa, "rows": rows},
    )
