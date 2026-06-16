"""EventLog 埋点测试"""
from app.models import EventLog, User


def test_log_event_writes_to_db(db):
    u = User(username="ev_user", password_hash=User.hash_password("x"), role="student", display_name="EV")
    db.add(u); db.commit(); db.refresh(u)
    from app.services.event_log_service import log_event
    log_event(db, u.id, "practice_start", {"subject": "数学", "count": 10})
    el = db.query(EventLog).filter(EventLog.user_id == u.id).first()
    assert el is not None
    assert el.event == "practice_start"
    assert "数学" in el.props


def test_log_event_non_blocking(db):
    """即使异常也不应抛出去"""
    from app.services.event_log_service import log_event
    log_event(None, 1, "test", {})  # should not raise
