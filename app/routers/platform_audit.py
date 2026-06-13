"""平台审计日志。"""
import csv
import io
from fastapi import APIRouter, Depends, Request
from fastapi.responses import Response
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import AuditLog, PlatformAdmin
from app.routers.platform_users import _require_platform


router = APIRouter(prefix="/platform")


@router.get("/audit-log")
def list_audit(
    request: Request,
    action: str = "",
    page: int = 1,
    db: Session = Depends(get_db),
    pa: PlatformAdmin = Depends(_require_platform),
):
    per_page = 50
    query = db.query(AuditLog)
    if action:
        query = query.filter(AuditLog.action == action)
    total = query.count()
    rows = query.order_by(AuditLog.id.desc()).offset((page - 1) * per_page).limit(per_page).all()
    return request.app.state.templates.TemplateResponse(
        "platform/audit_log.html",
        {"request": request, "pa": pa, "rows": rows, "action": action, "page": page, "total": total, "per_page": per_page},
    )


@router.get("/audit-log/export")
def export_audit(
    db: Session = Depends(get_db),
    pa: PlatformAdmin = Depends(_require_platform),
):
    rows = db.query(AuditLog).order_by(AuditLog.id.desc()).limit(5000).all()
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["id", "action", "target_type", "target_id", "actor_id", "detail", "created_at"])
    for r in rows:
        w.writerow([r.id, r.action, r.target_type, r.target_id, r.actor_id, r.detail, r.created_at])
    return Response(content=buf.getvalue(), media_type="text/csv", headers={"content-disposition": 'attachment; filename="audit_log.csv"'})
