"""Plan 2.2 — OnboardingState 模型 + onboarding API 测试"""
import pytest
from datetime import datetime
from app.models import OnboardingState, User
from fastapi.testclient import TestClient
from app.main import app as main_app
from app.core.security import create_access_token


def test_onboarding_state_creation(db):
    u = User(username="onboard_user", password_hash=User.hash_password("x"), role="student", display_name="OB")
    db.add(u); db.commit(); db.refresh(u)
    os = OnboardingState(user_id=u.id, step=0)
    db.add(os); db.commit(); db.refresh(os)
    assert os.step == 0
    assert os.user_id == u.id


def test_onboarding_state_unique_user(db):
    u = User(username="onboard_u2", password_hash=User.hash_password("x"), role="student", display_name="OB2")
    db.add(u); db.commit(); db.refresh(u)
    db.add(OnboardingState(user_id=u.id, step=1))
    db.commit()
    db.add(OnboardingState(user_id=u.id, step=2))
    with pytest.raises(Exception):
        db.commit()


def test_onboarding_state_default_step_zero(db):
    u = User(username="onboard_u3", password_hash=User.hash_password("x"), role="student", display_name="OB3")
    db.add(u); db.commit(); db.refresh(u)
    os = OnboardingState(user_id=u.id)
    db.add(os); db.commit(); db.refresh(os)
    assert os.step == 0
