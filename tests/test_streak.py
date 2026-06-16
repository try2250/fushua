"""Plan 2.1 — UserStreak model tests (TDD Task 2)"""
import pytest
from datetime import date
from app.models import UserStreak


def test_user_streak_creation(db):
    s = UserStreak(user_id=1, current_streak=3, max_streak=5, last_checkin_date=date.today())
    db.add(s); db.commit(); db.refresh(s)
    assert s.current_streak == 3
    assert s.max_streak == 5


def test_user_streak_defaults(db):
    s = UserStreak(user_id=999)
    db.add(s); db.commit(); db.refresh(s)
    assert s.current_streak == 0
    assert s.max_streak == 0
    assert s.last_checkin_date is None


def test_user_streak_unique_user(db, teacher_a):
    s1 = UserStreak(user_id=teacher_a.id)
    db.add(s1); db.commit()
    s2 = UserStreak(user_id=teacher_a.id)
    db.add(s2)
    with pytest.raises(Exception):
        db.commit()
