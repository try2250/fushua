"""Plan 2.1 — DailyCheckin 模型 + checkin_service 测试"""
import pytest
from datetime import date
from app.models import DailyCheckin, User


def test_daily_checkin_creation(db):
    u = User(username="student1", password_hash=User.hash_password("x"),
             role="student", display_name="S1")
    db.add(u); db.commit(); db.refresh(u)

    c = DailyCheckin(user_id=u.id, date=date.today(), question_count=3, is_checked=False)
    db.add(c); db.commit(); db.refresh(c)
    assert c.id is not None
    assert c.user_id == u.id
    assert c.question_count == 3


def test_daily_checkin_unique_user_date(db, teacher_a):
    c1 = DailyCheckin(user_id=teacher_a.id, date=date.today(), question_count=1)
    db.add(c1); db.commit()

    c2 = DailyCheckin(user_id=teacher_a.id, date=date.today(), question_count=2)
    db.add(c2)
    with pytest.raises(Exception):
        db.commit()
