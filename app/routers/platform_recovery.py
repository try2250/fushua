"""平台找回申请管理。"""
from datetime import datetime
from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, AccountRecoveryRequest, PlatformAdmin
from app.routers.platform_users import _require_platform


router = APIRouter(prefix="/platform")


@router.get("/recovery-requests")
def list_recovery(
    request: Request,
    db: Session = Depends(get_db),
    pa: PlatformAdmin = Depends(_require_platform),
):
    pending = db.query(AccountRecoveryRequest).filter(
        AccountRecoveryRequest.status == "pending"
    ).order_by(AccountRecoveryRequest.id.desc()).all()
    processed = db.query(AccountRecoveryRequest).filter(
        AccountRecoveryRequest.status != "pending"
    ).order_by(AccountRecoveryRequest.id.desc()).limit(50).all()
    return request.app.state.templates.TemplateResponse(
        "platform/recovery_requests.html",
        {"request": request, "pa": pa, "pending": pending, "processed": processed},
    )


@router.post("/recovery-requests/{request_id}/approve")
def approve_recovery(
    request_id: int,
    db: Session = Depends(get_db),
    pa: PlatformAdmin = Depends(_require_platform),
):
    req = db.query(AccountRecoveryRequest).filter(
        AccountRecoveryRequest.id == request_id
    ).first()
    if not req or req.status != "pending":
        raise HTTPException(status_code=404, detail="申请不存在或已处理")
    target = db.query(User).filter(User.username == req.username).first()
    if not target:
        raise HTTPException(status_code=404, detail="目标用户不存在")
    target.password_hash = User.hash_password("abc12345")
    target.force_password_change = True
    req.status = "approved"
    req.reviewed_at = datetime.utcnow()
    db.commit()
    return RedirectResponse(url="/platform/recovery-requests", status_code=303)


@router.post("/recovery-requests/{request_id}/reject")
def reject_recovery(
    request_id: int,
    db: Session = Depends(get_db),
    pa: PlatformAdmin = Depends(_require_platform),
):
    req = db.query(AccountRecoveryRequest).filter(
        AccountRecoveryRequest.id == request_id
    ).first()
    if not req or req.status != "pending":
        raise HTTPException(status_code=404, detail="申请不存在或已处理")
    req.status = "rejected"
    req.reviewed_at = datetime.utcnow()
    db.commit()
    return RedirectResponse(url="/platform/recovery-requests", status_code=303)
