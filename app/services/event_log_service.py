"""埋点服务 — 写 EventLog 表。"""
import json
import logging
from sqlalchemy.orm import Session
from app.models import EventLog


def log_event(db: Session, user_id: int, event: str, props: dict = None) -> None:
    try:
        if db is None:
            return
        el = EventLog(user_id=user_id, event=event, props=json.dumps(props or {}, ensure_ascii=False))
        db.add(el)
        db.commit()
    except Exception as e:
        logging.getLogger("fushua.event").warning(f"log_event failed (non-fatal): {e}")
