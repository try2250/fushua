"""E2E: 模拟 7 天答题 streak 逻辑"""
from datetime import date, timedelta
from fastapi.testclient import TestClient
from app.main import app as main_app
from app.models import User, Question, ClassGroup, ClassMember, DailyCheckin, UserStreak, WeeklyScore
from app.services.checkin_service import checkin_service


def test_7_day_streak_journey(db):
    """模拟学生在 7 天内每天答 5 题，验证 streak 和 checkin 逻辑。"""
    u = User(username="streak_student", password_hash=User.hash_password("x"), role="student", display_name="Streak")
    db.add(u); db.commit(); db.refresh(u)

    # Simulate 7 days
    for day_offset in range(7):
        today = date.today() - timedelta(days=6 - day_offset)
        for i in range(5):
            count_before = i
            count_after = i + 1
            checkin_service.increment_daily_count(db, u.id, today, count_before, count_after)

    # Verify checkins
    checkins = db.query(DailyCheckin).filter(DailyCheckin.user_id == u.id).all()
    assert len(checkins) == 7
    assert all(c.is_checked for c in checkins)

    # Verify streak
    streak = db.query(UserStreak).filter(UserStreak.user_id == u.id).first()
    assert streak is not None
    assert streak.current_streak == 7
    assert streak.max_streak == 7


def test_missed_day_resets_streak(db):
    """模拟连续 3 天→中断 1 天→再答，验证 streak 重置但 max 保留。"""
    u = User(username="miss_student", password_hash=User.hash_password("x"), role="student", display_name="Miss")
    db.add(u); db.commit(); db.refresh(u)

    # Day 1-3: consecutive
    for day_offset in range(3):
        d = date.today() - timedelta(days=4 - day_offset)
        checkin_service.increment_daily_count(db, u.id, d, 4, 5)

    s = db.query(UserStreak).filter(UserStreak.user_id == u.id).first()
    assert s.current_streak == 3
    assert s.max_streak == 3

    # Day 4: no activity (skip)

    # Day 5: answer again (today)
    checkin_service.increment_daily_count(db, u.id, date.today(), 4, 5)

    s = db.query(UserStreak).filter(UserStreak.user_id == u.id).first()
    assert s.current_streak == 1  # reset to day 1
    assert s.max_streak == 3  # max preserved
