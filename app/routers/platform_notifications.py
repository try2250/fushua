"""平台推送 dryrun 看板"""
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import NotificationDryrun, PlatformAdmin
from app.routers.platform_users import _require_platform
from sqlalchemy import desc

router = APIRouter(prefix="/platform")


@router.get("/notifications-dryrun")
def dryrun_page(request: Request, db: Session = Depends(get_db), pa: PlatformAdmin = Depends(_require_platform)):
    rows = db.query(NotificationDryrun).order_by(desc(NotificationDryrun.id)).limit(100).all()
    return request.app.state.templates.TemplateResponse("platform/notifications_dryrun.html", {"request": request, "pa": pa, "rows": rows})
