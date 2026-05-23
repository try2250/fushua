"""Audit logging utilities"""
from sqlalchemy.orm import Session
from app.models import AuditLog


def log_audit(db: Session, actor_id: int, action: str, target_type: str, target_id: int = None, metadata: dict = None):
    """Log an audit event"""
    audit_log = AuditLog(
        actor_id=actor_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        detail=metadata.get("detail", "") if metadata else ""
    )
    db.add(audit_log)
    # Note: caller should commit
