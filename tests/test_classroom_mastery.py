"""课堂错题与 MasteryRecord 打通 - 测试"""
import pytest
from app.core.security import create_access_token
from app.models import ClassGroup, ClassMember, Question, User, MasteryRecord
from tests.conftest import create_test_user


def _token(user):
    return create_access_token({
        "user_id": user.id,
        "role": user.role,
        "username": user.username,
    })


def test_draw_record_syncs_mastery_on_wrong(client, db_session):
    """答错时自动创建/更新 MasteryRecord 为 unmastered"""
    teacher = create_test_user(db_session, "mst_teacher", role="teacher")
    student = create_test_user(db_session, "mst_student", role="student")
    class_group = ClassGroup(name="测试班级-mastery", created_by=teacher.id)
    db_session.add(class_group)
    db_session.commit()
    db_session.refresh(class_group)
    db_session.add(ClassMember(class_id=class_group.id, user_id=student.id))
    q = Question(
        subject="数学", semester="八年级上册", chapter="代数",
        q_type="choice", difficulty=2, content="2+2=?",
        option_a="3", option_b="4", option_c="5", option_d="6",
        answer="B", explanation="2+2=4", created_by=teacher.id,
    )
    db_session.add(q)
    db_session.commit()
    db_session.refresh(q)

    # Create session
    resp = client.post(
        "/api/v1/classroom/sessions",
        headers={"Authorization": f"Bearer {_token(teacher)}"},
        json={"class_id": class_group.id, "title": "测试-mastery"}
    )
    assert resp.status_code == 200
    session_id = resp.json()["data"]["id"]

    # 答错
    client.post(
        f"/api/v1/classroom/sessions/{session_id}/draws",
        headers={"Authorization": f"Bearer {_token(teacher)}"},
        json={
            "student_id": student.id, "question_id": q.id,
            "result": "wrong", "score_delta": -1
        }
    )

    # 验证 mastery 表（使用 db_session — 与 API 共享同一个 SQLite 引擎）
    mastery = db_session.query(MasteryRecord).filter(
        MasteryRecord.user_id == student.id,
        MasteryRecord.question_id == q.id,
    ).first()
    assert mastery is not None, "应自动创建 MasteryRecord"
    assert mastery.status == "unmastered"
    assert mastery.consecutive_correct == 0


def test_draw_record_syncs_mastery_on_correct(client, db_session):
    """答对时自动更新 consecutive_correct，3次连对后标为 mastered"""
    teacher = create_test_user(db_session, "mst2_teacher", role="teacher")
    student = create_test_user(db_session, "mst2_student", role="student")
    class_group = ClassGroup(name="测试班级-mastery2", created_by=teacher.id)
    db_session.add(class_group)
    db_session.commit()
    db_session.refresh(class_group)
    db_session.add(ClassMember(class_id=class_group.id, user_id=student.id))
    q = Question(
        subject="数学", semester="八年级上册", chapter="代数",
        q_type="choice", difficulty=2, content="1+1=?",
        option_a="1", option_b="2", option_c="3", option_d="4",
        answer="B", explanation="1+1=2", created_by=teacher.id,
    )
    db_session.add(q)
    db_session.commit()
    db_session.refresh(q)

    resp = client.post(
        "/api/v1/classroom/sessions",
        headers={"Authorization": f"Bearer {_token(teacher)}"},
        json={"class_id": class_group.id, "title": "测试-mastery-correct"}
    )
    session_id = resp.json()["data"]["id"]

    # 答对 3 次
    for _ in range(3):
        client.post(
            f"/api/v1/classroom/sessions/{session_id}/draws",
            headers={"Authorization": f"Bearer {_token(teacher)}"},
            json={
                "student_id": student.id, "question_id": q.id,
                "result": "correct", "score_delta": 1
            }
        )

    mastery = db_session.query(MasteryRecord).filter(
        MasteryRecord.user_id == student.id,
        MasteryRecord.question_id == q.id,
    ).first()
    assert mastery is not None, "应自动创建 MasteryRecord"
    assert mastery.consecutive_correct == 3
    assert mastery.status == "mastered"


def test_draw_record_skip_does_not_create_mastery(client, db_session):
    """skip 操作不应创建 MasteryRecord"""
    teacher = create_test_user(db_session, "mst3_teacher", role="teacher")
    student = create_test_user(db_session, "mst3_student", role="student")
    class_group = ClassGroup(name="测试班级-mastery3", created_by=teacher.id)
    db_session.add(class_group)
    db_session.commit()
    db_session.refresh(class_group)
    db_session.add(ClassMember(class_id=class_group.id, user_id=student.id))
    q = Question(
        subject="数学", semester="八年级上册", chapter="代数",
        q_type="choice", difficulty=2, content="0+0=?",
        option_a="0", option_b="1", option_c="2", option_d="3",
        answer="A", explanation="0+0=0", created_by=teacher.id,
    )
    db_session.add(q)
    db_session.commit()
    db_session.refresh(q)

    resp = client.post(
        "/api/v1/classroom/sessions",
        headers={"Authorization": f"Bearer {_token(teacher)}"},
        json={"class_id": class_group.id, "title": "测试-mastery-skip"}
    )
    session_id = resp.json()["data"]["id"]

    # skip
    client.post(
        f"/api/v1/classroom/sessions/{session_id}/draws",
        headers={"Authorization": f"Bearer {_token(teacher)}"},
        json={
            "student_id": student.id, "question_id": q.id,
            "result": "skip", "score_delta": 0
        }
    )

    # skip should NOT create mastery record
    mastery = db_session.query(MasteryRecord).filter(
        MasteryRecord.user_id == student.id,
        MasteryRecord.question_id == q.id,
    ).first()
    assert mastery is None, "skip 不应创建 MasteryRecord"


def test_session_wrong_questions_endpoint(client, db_session):
    """错题端点正确聚合"""
    teacher = create_test_user(db_session, "wq_teacher", role="teacher")
    student = create_test_user(db_session, "wq_student", role="student")
    class_group = ClassGroup(name="测试班级-wrong-api", created_by=teacher.id)
    db_session.add(class_group)
    db_session.commit()
    db_session.refresh(class_group)
    db_session.add(ClassMember(class_id=class_group.id, user_id=student.id))

    q1 = Question(
        subject="数学", semester="八年级上册", chapter="代数",
        q_type="choice", difficulty=2, content="难题A",
        option_a="A", option_b="B", option_c="C", option_d="D",
        answer="B", explanation="...", created_by=teacher.id,
    )
    q2 = Question(
        subject="数学", semester="八年级上册", chapter="代数",
        q_type="choice", difficulty=2, content="难题B",
        option_a="A", option_b="B", option_c="C", option_d="D",
        answer="C", explanation="...", created_by=teacher.id,
    )
    db_session.add_all([q1, q2])
    db_session.commit()
    db_session.refresh(q1)
    db_session.refresh(q2)

    resp = client.post(
        "/api/v1/classroom/sessions",
        headers={"Authorization": f"Bearer {_token(teacher)}"},
        json={"class_id": class_group.id, "title": "测试-wrong-api"}
    )
    session_id = resp.json()["data"]["id"]

    # q1 答错2次, q2 答错1次
    for _ in range(2):
        client.post(
            f"/api/v1/classroom/sessions/{session_id}/draws",
            headers={"Authorization": f"Bearer {_token(teacher)}"},
            json={"student_id": student.id, "question_id": q1.id, "result": "wrong", "score_delta": -1}
        )
    client.post(
        f"/api/v1/classroom/sessions/{session_id}/draws",
        headers={"Authorization": f"Bearer {_token(teacher)}"},
        json={"student_id": student.id, "question_id": q2.id, "result": "wrong", "score_delta": -1}
    )

    resp = client.get(
        f"/api/v1/classroom/sessions/{session_id}/wrong-questions",
        headers={"Authorization": f"Bearer {_token(teacher)}"},
    )
    assert resp.status_code == 200
    data = resp.json().get("data", resp.json())
    assert data["total_wrong"] == 3
    assert data["distinct_questions"] == 2

    # 按 wrong_count 降序，q1 应排第一
    assert data["wrong_questions"][0]["wrong_count"] == 2
    assert data["wrong_questions"][0]["question_id"] == q1.id


def test_class_classroom_wrong_questions_endpoint(client, db_session):
    """班级错题汇总端点"""
    teacher = create_test_user(db_session, "cwq_teacher", role="teacher")
    student = create_test_user(db_session, "cwq_student", role="student")
    class_group = ClassGroup(name="测试班级-cwq", created_by=teacher.id)
    db_session.add(class_group)
    db_session.commit()
    db_session.refresh(class_group)
    db_session.add(ClassMember(class_id=class_group.id, user_id=student.id))

    q = Question(
        subject="数学", semester="八年级上册", chapter="代数",
        q_type="choice", difficulty=2, content="班级错题测试",
        option_a="A", option_b="B", option_c="C", option_d="D",
        answer="B", explanation="...", created_by=teacher.id,
    )
    db_session.add(q)
    db_session.commit()
    db_session.refresh(q)

    resp = client.post(
        "/api/v1/classroom/sessions",
        headers={"Authorization": f"Bearer {_token(teacher)}"},
        json={"class_id": class_group.id, "title": "测试-cwq"}
    )
    session_id = resp.json()["data"]["id"]

    client.post(
        f"/api/v1/classroom/sessions/{session_id}/draws",
        headers={"Authorization": f"Bearer {_token(teacher)}"},
        json={"student_id": student.id, "question_id": q.id, "result": "wrong", "score_delta": -1}
    )

    resp = client.get(
        f"/api/v1/classroom/classes/{class_group.id}/classroom-wrong-questions?days=30",
        headers={"Authorization": f"Bearer {_token(teacher)}"},
    )
    assert resp.status_code == 200
    data = resp.json().get("data", resp.json())
    assert data["class_id"] == class_group.id
    assert data["total_wrong_records"] >= 1
    assert data["distinct_questions"] >= 1
    assert data["wrong_questions"][0]["affected_students"] >= 1
