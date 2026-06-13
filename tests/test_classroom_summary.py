"""课堂总结与积分榜 - 测试"""
import pytest
from app.core.security import create_access_token
from app.models import ClassGroup, ClassMember, Question, User
from tests.conftest import create_test_user


def _token(user):
    return create_access_token({
        "user_id": user.id,
        "role": user.role,
        "username": user.username,
    })


def test_classroom_summary_returns_empty_when_no_draws(client, db_session):
    """无抽答记录时 summary 返回空积分榜"""
    teacher = create_test_user(db_session, "sum_teacher", role="teacher")
    student = create_test_user(db_session, "sum_student", role="student")
    class_group = ClassGroup(name="测试班级-summary", created_by=teacher.id)
    db_session.add(class_group)
    db_session.commit()
    db_session.refresh(class_group)
    db_session.add(ClassMember(class_id=class_group.id, user_id=student.id))
    db_session.commit()

    # 创建课堂
    resp = client.post(
        "/api/v1/classroom/sessions",
        headers={"Authorization": f"Bearer {_token(teacher)}"},
        json={"class_id": class_group.id, "title": "测试课堂-summary"}
    )
    assert resp.status_code == 200
    session_id = resp.json()["data"]["id"]

    resp = client.get(
        f"/api/v1/classroom/sessions/{session_id}/summary",
        headers={"Authorization": f"Bearer {_token(teacher)}"},
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["total_draws"] == 0
    assert data["correct_count"] == 0
    assert data["scoreboard"] == []


def test_classroom_summary_with_draws(client, db_session):
    """有抽答记录时 summary 正确聚合"""
    teacher = create_test_user(db_session, "sum_teacher2", role="teacher")
    student = create_test_user(db_session, "sum_student2", role="student")
    class_group = ClassGroup(name="测试班级-summary2", created_by=teacher.id)
    db_session.add(class_group)
    db_session.commit()
    db_session.refresh(class_group)
    db_session.add(ClassMember(class_id=class_group.id, user_id=student.id))
    db_session.commit()

    student_id = student.id

    # 创建课堂
    resp = client.post(
        "/api/v1/classroom/sessions",
        headers={"Authorization": f"Bearer {_token(teacher)}"},
        json={"class_id": class_group.id, "title": "测试课堂-summary2"}
    )
    assert resp.status_code == 200
    session_id = resp.json()["data"]["id"]

    # 添加几条抽答记录
    client.post(
        f"/api/v1/classroom/sessions/{session_id}/draws",
        headers={"Authorization": f"Bearer {_token(teacher)}"},
        json={"student_id": student_id, "result": "correct", "score_delta": 1}
    )
    client.post(
        f"/api/v1/classroom/sessions/{session_id}/draws",
        headers={"Authorization": f"Bearer {_token(teacher)}"},
        json={"student_id": student_id, "result": "wrong", "score_delta": -1}
    )
    client.post(
        f"/api/v1/classroom/sessions/{session_id}/draws",
        headers={"Authorization": f"Bearer {_token(teacher)}"},
        json={"student_id": student_id, "result": "correct", "score_delta": 2}
    )

    # 获取 summary
    resp = client.get(
        f"/api/v1/classroom/sessions/{session_id}/summary",
        headers={"Authorization": f"Bearer {_token(teacher)}"},
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["total_draws"] == 3
    assert data["correct_count"] == 2
    assert data["wrong_count"] == 1
    assert len(data["scoreboard"]) >= 1

    # 验证积分榜
    top_student = data["scoreboard"][0]
    assert top_student["student_id"] == student_id
    assert top_student["score"] == 2  # 1 + (-1) + 2 = 2
    assert top_student["draw_count"] == 3
    assert top_student["correct_count"] == 2
    assert top_student["wrong_count"] == 1
