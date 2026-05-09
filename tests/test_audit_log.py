import pytest
from app.models import AuditLog
from tests.conftest import create_test_user


def test_create_audit_log(db_session):
    user = create_test_user(db_session, username="admin", role="teacher")

    log = AuditLog(
        actor_id=user.id,
        action="create_question",
        target_type="question",
        target_id=1,
        detail='{"subject": "数学", "chapter": "代数"}'
    )
    db_session.add(log)
    db_session.commit()

    result = db_session.query(AuditLog).filter(AuditLog.id == log.id).first()
    assert result is not None
    assert result.actor_id == user.id
    assert result.action == "create_question"
    assert result.target_type == "question"
    assert result.target_id == 1
    assert result.detail == '{"subject": "数学", "chapter": "代数"}'
    assert result.created_at is not None


def test_query_by_action(db_session):
    create_test_user(db_session, username="user1", role="student")

    logs = [
        AuditLog(actor_id=1, action="login", target_type="", detail="用户登录"),
        AuditLog(actor_id=1, action="create_question", target_type="question", detail="创建题目"),
        AuditLog(actor_id=1, action="create_question", target_type="question", detail="再创建题目"),
    ]
    for log in logs:
        db_session.add(log)
    db_session.commit()

    action_logs = db_session.query(AuditLog).filter(AuditLog.action == "create_question").all()
    assert len(action_logs) == 2
    assert all(log.action == "create_question" for log in action_logs)


def test_query_by_actor_id(db_session):
    user1 = create_test_user(db_session, username="user_a", role="student")
    user2 = create_test_user(db_session, username="user_b", role="teacher")

    db_session.add(AuditLog(actor_id=user1.id, action="login", detail="user_a登录"))
    db_session.add(AuditLog(actor_id=user1.id, action="practice", detail="user_a练习"))
    db_session.add(AuditLog(actor_id=user2.id, action="login", detail="user_b登录"))
    db_session.commit()

    user1_logs = db_session.query(AuditLog).filter(AuditLog.actor_id == user1.id).all()
    assert len(user1_logs) == 2
    assert all(log.actor_id == user1.id for log in user1_logs)

    user2_logs = db_session.query(AuditLog).filter(AuditLog.actor_id == user2.id).all()
    assert len(user2_logs) == 1
    assert user2_logs[0].actor_id == user2.id
