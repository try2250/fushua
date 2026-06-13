"""班级积分榜 - 测试"""
from app.core.security import create_access_token
from app.models import ClassGroup, ClassMember
from tests.conftest import create_test_user


def _token(user):
    return create_access_token({
        "user_id": user.id, "role": user.role, "username": user.username,
    })


def _parse_body(resp):
    """兼容裸 dict 和 ResponseModel 包装两种返回格式"""
    body = resp.json()
    return body.get("data", body)


def test_class_scoreboard_aggregates_across_sessions(client, db_session):
    """跨课堂积分榜正确聚合"""
    teacher = create_test_user(db_session, "sb_teacher", role="teacher")
    stu_a = create_test_user(db_session, "sb_stu_a", role="student")
    stu_b = create_test_user(db_session, "sb_stu_b", role="student")
    cg = ClassGroup(name="积分榜测试班", created_by=teacher.id)
    db_session.add(cg); db_session.commit(); db_session.refresh(cg)
    db_session.add(ClassMember(class_id=cg.id, user_id=stu_a.id))
    db_session.add(ClassMember(class_id=cg.id, user_id=stu_b.id))
    db_session.commit()

    token = _token(teacher)
    s1 = client.post("/api/v1/classroom/sessions", headers={"Authorization": f"Bearer {token}"},
        json={"class_id": cg.id, "title": "A"}).json()["data"]["id"]
    client.post(f"/api/v1/classroom/sessions/{s1}/draws", headers={"Authorization": f"Bearer {token}"},
        json={"student_id": stu_a.id, "result": "correct", "score_delta": 2})
    s2 = client.post("/api/v1/classroom/sessions", headers={"Authorization": f"Bearer {token}"},
        json={"class_id": cg.id, "title": "B"}).json()["data"]["id"]
    client.post(f"/api/v1/classroom/sessions/{s2}/draws", headers={"Authorization": f"Bearer {token}"},
        json={"student_id": stu_a.id, "result": "correct", "score_delta": 1})
    client.post(f"/api/v1/classroom/sessions/{s2}/draws", headers={"Authorization": f"Bearer {token}"},
        json={"student_id": stu_b.id, "result": "wrong", "score_delta": -1})

    resp = client.get(f"/api/v1/classroom/classes/{cg.id}/scoreboard?days=30",
        headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = _parse_body(resp)
    assert data["total_draws"] == 3
    assert data["total_students"] == 2
    sb = data["scoreboard"]
    assert sb[0]["score"] == 3    # stu_a: +2 +1
    assert sb[1]["score"] == -1   # stu_b: -1


def test_class_scoreboard_includes_zero_score_students(client, db_session):
    """零分学生也出现在积分榜"""
    teacher = create_test_user(db_session, "sb2_teacher", role="teacher")
    stu = create_test_user(db_session, "sb2_stu", role="student")
    zero = create_test_user(db_session, "sb2_zero", role="student")
    cg = ClassGroup(name="零分班", created_by=teacher.id)
    db_session.add(cg); db_session.commit(); db_session.refresh(cg)
    db_session.add(ClassMember(class_id=cg.id, user_id=stu.id))
    db_session.add(ClassMember(class_id=cg.id, user_id=zero.id))
    db_session.commit()

    token = _token(teacher)
    s = client.post("/api/v1/classroom/sessions", headers={"Authorization": f"Bearer {token}"},
        json={"class_id": cg.id, "title": "单次课"}).json()["data"]["id"]
    client.post(f"/api/v1/classroom/sessions/{s}/draws", headers={"Authorization": f"Bearer {token}"},
        json={"student_id": stu.id, "result": "correct", "score_delta": 1})

    resp = client.get(f"/api/v1/classroom/classes/{cg.id}/scoreboard?days=30",
        headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = _parse_body(resp)
    assert data["total_students"] == 2
    assert len(data["scoreboard"]) == 2
    ids = [s["student_id"] for s in data["scoreboard"]]
    assert zero.id in ids
