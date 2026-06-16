"""Plan 2.1 — DailyCheckin 模型 + checkin_service 测试"""
import pytest
from datetime import date, timedelta
from app.models import DailyCheckin, User, UserStreak


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


# ─── Plan 2.1 checkin_service tests (TDD Task 4) ───
from app.services.checkin_service import checkin_service


def test_increment_creates_checkin(db):
    checkin_service.increment_daily_count(db, user_id=999, today=date.today(), count_before=0, count_after=3)
    c = db.query(DailyCheckin).filter(DailyCheckin.user_id == 999).first()
    assert c is not None
    assert c.question_count == 3
    assert c.is_checked == False


def test_increment_5_questions_triggers_check(db):
    checkin_service.increment_daily_count(db, user_id=998, today=date.today(), count_before=4, count_after=5)
    c = db.query(DailyCheckin).filter(DailyCheckin.user_id == 998).first()
    assert c.is_checked == True
    assert c.question_count == 5


def test_checkin_creates_streak_first_time(db):
    checkin_service.increment_daily_count(db, user_id=997, today=date.today(), count_before=4, count_after=5)
    s = db.query(UserStreak).filter(UserStreak.user_id == 997).first()
    assert s is not None
    assert s.current_streak == 1
    assert s.max_streak == 1
    assert s.last_checkin_date == date.today()


def test_consecutive_checkin_increments_streak(db):
    yesterday = date.today() - timedelta(days=1)
    db.add(UserStreak(user_id=996, current_streak=2, max_streak=5, last_checkin_date=yesterday))
    db.commit()
    checkin_service.increment_daily_count(db, user_id=996, today=date.today(), count_before=4, count_after=5)
    s = db.query(UserStreak).filter(UserStreak.user_id == 996).first()
    assert s.current_streak == 3


def test_missed_day_resets_streak(db):
    two_days_ago = date.today() - timedelta(days=2)
    db.add(UserStreak(user_id=995, current_streak=5, max_streak=10, last_checkin_date=two_days_ago))
    db.commit()
    checkin_service.increment_daily_count(db, user_id=995, today=date.today(), count_before=4, count_after=5)
    s = db.query(UserStreak).filter(UserStreak.user_id == 995).first()
    assert s.current_streak == 1  # reset to 1 because today IS day 1
    assert s.max_streak == 10  # max preserved


# ─── Plan 2.1 integration test (TDD Task 6) ───

def test_record_creation_triggers_checkin(db, teacher_a):
    """Create 5 records via record_service → should trigger checkin + streak."""
    from app.models import Record, Question, DailyCheckin, UserStreak
    from app.schemas.record import RecordCreate
    from app.services.record_service import record_service

    q = Question(subject="数学", semester="七年级上册", chapter="代数", q_type="choice",
                 content="1+1=?", option_a="1", option_b="2", option_c="3", option_d="4",
                 answer="B", created_by=teacher_a.id)
    db.add(q); db.commit(); db.refresh(q)

    for i in range(5):
        rc = RecordCreate(question_id=q.id, user_answer="B", is_correct=True)
        record_service.create_record(db, rc, teacher_a.id)

    c = db.query(DailyCheckin).filter(
        DailyCheckin.user_id == teacher_a.id, DailyCheckin.date == date.today()
    ).first()
    assert c is not None
    assert c.is_checked == True
    assert c.question_count >= 5
