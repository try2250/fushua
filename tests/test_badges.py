"""Plan 2.2 — Badge + UserBadge 模型 + badge_service 测试"""
import pytest
from datetime import datetime
from app.models import Badge, UserBadge, User


def test_badge_creation(db):
    b = Badge(code="opening", name="开门红", description="首次答题", icon_url="/static/badges/opening.png")
    db.add(b); db.commit(); db.refresh(b)
    assert b.id is not None
    assert b.code == "opening"


def test_badge_code_unique(db):
    db.add(Badge(code="streak_3", name="三日连击"))
    db.commit()
    db.add(Badge(code="streak_3", name="dup"))
    with pytest.raises(Exception):
        db.commit()


def test_user_badge_creation(db):
    u = User(username="badge_user", password_hash=User.hash_password("x"), role="student", display_name="BU")
    db.add(u); db.commit(); db.refresh(u)
    b = Badge(code="hundred", name="百题成就")
    db.add(b); db.commit(); db.refresh(b)
    ub = UserBadge(user_id=u.id, badge_id=b.id)
    db.add(ub); db.commit(); db.refresh(ub)
    assert ub.id is not None
    assert ub.earned_at is not None


def test_user_badge_unique_user_badge(db):
    u = User(username="ub_user", password_hash=User.hash_password("x"), role="student", display_name="UB2")
    db.add(u); db.commit(); db.refresh(u)
    b = Badge(code="thousand", name="千题成就")
    db.add(b); db.commit(); db.refresh(b)
    db.add(UserBadge(user_id=u.id, badge_id=b.id))
    db.commit()
    db.add(UserBadge(user_id=u.id, badge_id=b.id))
    with pytest.raises(Exception):
        db.commit()
