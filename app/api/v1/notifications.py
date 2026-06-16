"""通知中心 API"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.deps import get_current_user
from app.models import InboxMessage, User
from app.schemas.common import ResponseModel

router = APIRouter(prefix="/notifications", tags=["通知"])


@router.get("", response_model=ResponseModel[list])
def list_inbox(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    rows = db.query(InboxMessage).filter(InboxMessage.user_id == current_user.id).order_by(InboxMessage.id.desc()).limit(50).all()
    return ResponseModel(data=[{"id": r.id, "title": r.title, "body": r.body, "type": r.type, "is_read": r.is_read, "created_at": str(r.created_at)} for r in rows])


@router.post("/{msg_id}/read", response_model=ResponseModel[dict])
def mark_read(msg_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    im = db.query(InboxMessage).filter(InboxMessage.id == msg_id, InboxMessage.user_id == current_user.id).first()
    if not im:
        raise HTTPException(status_code=404, detail="通知不存在")
    im.is_read = True
    db.commit()
    return ResponseModel(data={"ok": True})
