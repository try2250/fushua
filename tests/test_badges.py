"""Plan 2.2 — Badge + UserBadge 模型 + badge_service 测试"""
import pytest
from datetime import datetime
from app.models import Badge, UserBadge, User


BADGE_SEEDS = [
    ("opening", "开门红", "首次答题"),
    ("streak_3", "三日连击", "连续打卡 3 天"),
    ("streak_7", "七日不缀", "连续打卡 7 天"),
    ("streak_30", "三十日大师", "连续打卡 30 天"),
    ("hundred", "百题成就", "累计答对 100 题"),
    ("thousand", "千题成就", "累计答对 1000 题"),
    ("perfect_set", "满分组", "一组 10 题全对"),
    ("subject_math", "数学开光", "数学正确率 >= 80% 且 >= 50 题"),
    ("subject_physics", "物理开光", "物理正确率 >= 80% 且 >= 50 题"),
    ("subject_chinese", "语文开光", "语文正确率 >= 80% 且 >= 50 题"),
]


@pytest.fixture
def seeded_badges(db):
    """Seed 10 badges before testing badge_service."""
    for code, name, desc in BADGE_SEEDS:
        if not db.query(Badge).filter(Badge.code == code).first():
            db.add(Badge(code=code, name=name, description=desc,
                        icon_url=f"/static/badges/{code}.png"))
    db.commit()


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


from app.services.badge_service import badge_service


def test_check_and_grant_opening_badge(db, seeded_badges):
    u = User(username="b1", password_hash=User.hash_password("x"), role="student", display_name="B1")
    db.add(u); db.commit(); db.refresh(u)
    badge_service.check_and_grant(db, u.id, "answer_submit", {"total_answers": 1})
    ub = db.query(UserBadge).filter(UserBadge.user_id == u.id).first()
    assert ub is not None


def test_check_and_grant_streak_3(db, seeded_badges):
    u = User(username="b2", password_hash=User.hash_password("x"), role="student", display_name="B2")
    db.add(u); db.commit(); db.refresh(u)
    badge_service.check_and_grant(db, u.id, "streak_change", {"streak": 3})
    ub = db.query(UserBadge).filter(UserBadge.user_id == u.id).first()
    assert ub is not None


def test_check_and_grant_no_duplicate(db, seeded_badges):
    u = User(username="b3", password_hash=User.hash_password("x"), role="student", display_name="B3")
    db.add(u); db.commit(); db.refresh(u)
    badge_service.check_and_grant(db, u.id, "answer_submit", {"total_answers": 1})
    # Grant again — should be idempotent
    badge_service.check_and_grant(db, u.id, "answer_submit", {"total_answers": 1})
    count = db.query(UserBadge).filter(UserBadge.user_id == u.id).count()
    assert count == 1


def test_check_and_grant_hundred(db, seeded_badges):
    u = User(username="b4", password_hash=User.hash_password("x"), role="student", display_name="B4")
    db.add(u); db.commit(); db.refresh(u)
    badge_service.check_and_grant(db, u.id, "answer_submit", {"total_answers": 100})
    ub = db.query(UserBadge).filter(UserBadge.user_id == u.id).count()
    assert ub >= 2  # opening + hundred


def test_record_creation_grants_opening_badge(db, seeded_badges, teacher_a):
    from app.models import Question, Record
    from app.schemas.record import RecordCreate
    q = Question(subject="数学", semester="七年级上册", chapter="代数", q_type="choice",
                 content="1+1=?", option_a="1", option_b="2", option_c="3", option_d="4",
                 answer="B", created_by=teacher_a.id)
    db.add(q); db.commit(); db.refresh(q)
    from app.services.record_service import record_service
    record_service.create_record(db, RecordCreate(question_id=q.id, user_answer="B", is_correct=True), teacher_a.id)
    ub = db.query(UserBadge).filter(UserBadge.user_id == teacher_a.id).first()
    assert ub is not None  # opening badge granted


def test_badges_api_returns_all_badges(client, db, teacher_a, seeded_badges):
    from app.core.security import create_access_token
    token = create_access_token({"user_id": teacher_a.id})
    r = client.get("/api/v1/badges/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    data = r.json()["data"]
    assert len(data) == 10
