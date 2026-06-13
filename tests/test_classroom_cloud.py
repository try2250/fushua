"""课堂伴侣云端唯一化 - 后端测试"""
from app.core.security import create_access_token
from app.models import ClassGroup, ClassMember, Question, User
from tests.conftest import create_test_user


def _token(user):
    return create_access_token({
        "user_id": user.id,
        "role": user.role,
        "username": user.username,
    })


def test_classroom_bootstrap_returns_teacher_cloud_data(client, db_session):
    """bootstrap 端点返回教师的云端数据"""
    teacher = create_test_user(db_session, "cloud_teacher", role="teacher")
    student = create_test_user(db_session, "cloud_student", role="student")
    class_group = ClassGroup(name="云端一班", created_by=teacher.id)
    db_session.add(class_group)
    db_session.commit()
    db_session.refresh(class_group)
    db_session.add(ClassMember(class_id=class_group.id, user_id=student.id))
    db_session.add(Question(
        subject="数学",
        semester="八年级上册",
        chapter="代数",
        q_type="choice",
        difficulty=2,
        content="1+1=?",
        option_a="1",
        option_b="2",
        option_c="3",
        option_d="4",
        answer="B",
        explanation="1+1=2",
        created_by=teacher.id,
    ))
    db_session.commit()

    response = client.get(
        "/api/v1/classroom/bootstrap",
        headers={"Authorization": f"Bearer {_token(teacher)}"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["code"] == 0
    assert body["data"]["classes"][0]["name"] == "云端一班"
    assert body["data"]["active_session"] is None
    assert body["data"]["local_storage_business_keys"] == []


def test_classroom_session_state_round_trip(client, db_session):
    """课堂会话状态的保存和恢复往返测试"""
    teacher = create_test_user(db_session, "state_teacher", role="teacher")
    class_group = ClassGroup(name="状态班", created_by=teacher.id)
    db_session.add(class_group)
    db_session.commit()
    db_session.refresh(class_group)

    token = _token(teacher)
    session_response = client.post(
        "/api/v1/classroom/sessions",
        json={"class_id": class_group.id, "title": "状态课", "mode": "normal"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert session_response.status_code == 200
    session_id = session_response.json()["data"]["id"]

    state_payload = {
        "active_view": "SESSION",
        "selected_student_id": None,
        "selected_question_id": None,
        "group_set_id": None,
    }
    save_response = client.patch(
        f"/api/v1/classroom/sessions/{session_id}/state",
        json={"state": state_payload, "version": 1},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert save_response.status_code == 200

    get_response = client.get(
        f"/api/v1/classroom/sessions/{session_id}/state",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert get_response.status_code == 200
    assert get_response.json()["data"]["state"] == state_payload
    assert get_response.json()["data"]["version"] == 1


def test_classroom_draw_record_persists_to_cloud(client, db_session):
    """课堂抽答记录持久化到云端"""
    teacher = create_test_user(db_session, "draw_teacher", role="teacher")
    student = create_test_user(db_session, "draw_student", role="student")
    class_group = ClassGroup(name="抽答班", created_by=teacher.id)
    db_session.add(class_group)
    db_session.commit()
    db_session.refresh(class_group)
    db_session.add(ClassMember(class_id=class_group.id, user_id=student.id))
    question = Question(
        subject="数学",
        semester="八年级上册",
        chapter="代数",
        q_type="choice",
        difficulty=2,
        content="2+2=?",
        option_a="3",
        option_b="4",
        option_c="5",
        option_d="6",
        answer="B",
        explanation="2+2=4",
        created_by=teacher.id,
    )
    db_session.add(question)
    db_session.commit()
    db_session.refresh(question)

    token = _token(teacher)
    session_id = client.post(
        "/api/v1/classroom/sessions",
        json={"class_id": class_group.id, "title": "抽答课", "mode": "normal"},
        headers={"Authorization": f"Bearer {token}"},
    ).json()["data"]["id"]

    response = client.post(
        f"/api/v1/classroom/sessions/{session_id}/draws",
        json={
            "student_id": student.id,
            "question_id": question.id,
            "result": "wrong",
            "score_delta": -1,
            "note": "课堂答错",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["student_id"] == student.id
    assert data["question_id"] == question.id
    assert data["result"] == "wrong"

    list_response = client.get(
        f"/api/v1/classroom/sessions/{session_id}/draws",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert list_response.status_code == 200
    assert list_response.json()["data"][0]["note"] == "课堂答错"
