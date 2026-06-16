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


from app.services.notification_service import notification_service
from datetime import datetime


def test_daily_push_creates_dryrun_records(db):
    u = User(username="push_user", password_hash=User.hash_password("x"), role="student", display_name="PU")
    db.add(u); db.commit(); db.refresh(u)
    notification_service.create_push_for_user(db, u.id, "daily_checkin", {"count": 5}, datetime.utcnow())
    dr = db.query(NotificationDryrun).filter(NotificationDryrun.user_id == u.id).first()
    assert dr is not None
    assert dr.template == "daily_checkin"


def test_create_inbox_for_user(db):
    u = User(username="inbox_user", password_hash=User.hash_password("x"), role="student", display_name="IU")
    db.add(u); db.commit(); db.refresh(u)
    notification_service.create_inbox(db, u.id, "daily_checkin", "每日打卡提醒", "你今天完成了5题！")
    im = db.query(InboxMessage).filter(InboxMessage.user_id == u.id).first()
    assert im is not None
    assert im.title == "每日打卡提醒"


from fastapi.testclient import TestClient
from app.main import app as main_app
from app.core.security import create_access_token


def test_notifications_api_returns_inbox(client, db, teacher_a):
    db.add(InboxMessage(user_id=teacher_a.id, title="test", body="hello", type="daily_checkin"))
    db.commit()
    token = create_access_token({"user_id": teacher_a.id})
    r = client.get("/api/v1/notifications", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    data = r.json()["data"]
    assert len(data) >= 1
    assert data[0]["title"] == "test"


def test_notifications_mark_read(client, db, teacher_a):
    im = InboxMessage(user_id=teacher_a.id, title="read", body="me", type="test")
    db.add(im); db.commit(); db.refresh(im)
    token = create_access_token({"user_id": teacher_a.id})
    r = client.post(f"/api/v1/notifications/{im.id}/read", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    db.refresh(im)
    assert im.is_read == True
