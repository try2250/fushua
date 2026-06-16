"""Plan 2.3 — NotificationDryrun + InboxMessage + EventLog 模型测试"""
import pytest
from datetime import datetime
from app.models import NotificationDryrun, InboxMessage, EventLog, User


def test_notification_dryrun_creation(db):
    u = User(username="nd_user", password_hash=User.hash_password("x"), role="student", display_name="ND")
    db.add(u); db.commit(); db.refresh(u)
    nd = NotificationDryrun(user_id=u.id, template="daily_checkin", payload='{"count":5}',
                           scheduled_at=datetime.utcnow())
    db.add(nd); db.commit(); db.refresh(nd)
    assert nd.id is not None
    assert nd.template == "daily_checkin"
    assert nd.delivered == False


def test_inbox_message_creation(db):
    u = User(username="im_user", password_hash=User.hash_password("x"), role="student", display_name="IM")
    db.add(u); db.commit(); db.refresh(u)
    im = InboxMessage(user_id=u.id, title="今日打卡", body="完成5题！", type="daily_checkin")
    db.add(im); db.commit(); db.refresh(im)
    assert im.id is not None
    assert im.is_read == False


def test_event_log_creation(db):
    u = User(username="el_user", password_hash=User.hash_password("x"), role="student", display_name="EL")
    db.add(u); db.commit(); db.refresh(u)
    el = EventLog(user_id=u.id, event="practice_start", props='{"subject":"数学"}')
    db.add(el); db.commit(); db.refresh(el)
    assert el.id is not None
    assert el.event == "practice_start"
