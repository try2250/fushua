"""Plan 4.1 — 真实推送 + E2E 测试"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
from app.models import User, NotificationDryrun, InboxMessage
from app.services.wechat_push_service import wechat_push_service


def test_daily_push_real_marks_dryrun_as_sent(db, teacher_a):
    """daily_push_real 扫描未发记录，调 wechat send 并标记 sent_at。"""
    nd = NotificationDryrun(
        user_id=teacher_a.id, template="daily_checkin",
        payload='{"count":5}', scheduled_at=datetime.utcnow(),
    )
    db.add(nd); db.commit(); db.refresh(nd)

    fake_resp = MagicMock()
    fake_resp.json.return_value = {"errcode": 0, "errmsg": "ok"}

    # Pre-set access token so _get_access_token doesn't make real HTTP call
    wechat_push_service._access_token = "mock_token"
    wechat_push_service._token_expires_at = 9999999999

    with patch("app.services.wechat_push_service.httpx.post", return_value=fake_resp):
        from app.services.notification_service import daily_push_real
        daily_push_real(db=db)

    db.expire_all()
    db.refresh(nd)
    assert nd.sent_at is not None
    assert nd.delivered is True


def test_daily_push_real_creates_inbox(db, teacher_a):
    """真实推送后应写 InboxMessage。"""
    nd = NotificationDryrun(
        user_id=teacher_a.id, template="daily_checkin",
        payload='{"count":3}', scheduled_at=datetime.utcnow(),
    )
    db.add(nd); db.commit()

    fake_resp = MagicMock()
    fake_resp.json.return_value = {"errcode": 0}

    wechat_push_service._access_token = "mock_token"
    wechat_push_service._token_expires_at = 9999999999

    with patch("app.services.wechat_push_service.httpx.post", return_value=fake_resp):
        from app.services.notification_service import daily_push_real
        daily_push_real(db=db)

    ims = db.query(InboxMessage).filter(InboxMessage.user_id == teacher_a.id).all()
    assert len(ims) >= 1
