import pytest
from tests.conftest import create_test_user
from app.models import Assignment
from app.core.security import create_access_token


def test_create_assignment_as_teacher(client, db_session):
    teacher = create_test_user(db_session, "teacher1", role="teacher")
    token = create_access_token({"user_id": teacher.id, "role": teacher.role, "username": teacher.username})

    response = client.post(
        "/api/v1/assignments",
        json={
            "title": "数学作业1",
            "description": "完成第一章习题",
            "question_ids": "1,2,3",
            "class_id": 1
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 0
    assert data["data"]["title"] == "数学作业1"


def test_create_assignment_as_student_fails(client, db_session):
    student = create_test_user(db_session, "student1", role="student")
    token = create_access_token({"user_id": student.id, "role": student.role, "username": student.username})

    response = client.post(
        "/api/v1/assignments",
        json={
            "title": "作业",
            "question_ids": "1,2,3"
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 403


def test_get_assignments_as_teacher(client, db_session):
    teacher = create_test_user(db_session, "teacher1", role="teacher")
    token = create_access_token({"user_id": teacher.id, "role": teacher.role, "username": teacher.username})

    assignment1 = Assignment(title="作业1", question_ids="1,2", created_by=teacher.id)
    assignment2 = Assignment(title="作业2", question_ids="3,4", created_by=teacher.id)
    db_session.add_all([assignment1, assignment2])
    db_session.commit()

    response = client.get(
        "/api/v1/assignments",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 2


def test_submit_assignment(client, db_session):
    teacher = create_test_user(db_session, "teacher1", role="teacher")
    student = create_test_user(db_session, "student1", role="student")
    student_token = create_access_token({"user_id": student.id, "role": student.role, "username": student.username})

    assignment = Assignment(title="作业1", question_ids="1,2,3", created_by=teacher.id)
    db_session.add(assignment)
    db_session.commit()
    db_session.refresh(assignment)

    response = client.post(
        f"/api/v1/assignments/{assignment.id}/submit",
        json={"answers": {"1": "A", "2": "B", "3": "C"}},
        headers={"Authorization": f"Bearer {student_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["completed"] == True


def test_get_assignment_records(client, db_session):
    teacher = create_test_user(db_session, "teacher1", role="teacher")
    student = create_test_user(db_session, "student1", role="student")
    teacher_token = create_access_token({"user_id": teacher.id, "role": teacher.role, "username": teacher.username})
    student_token = create_access_token({"user_id": student.id, "role": student.role, "username": student.username})

    assignment = Assignment(title="作业1", question_ids="1,2,3", created_by=teacher.id)
    db_session.add(assignment)
    db_session.commit()
    db_session.refresh(assignment)

    client.post(
        f"/api/v1/assignments/{assignment.id}/submit",
        json={"answers": {"1": "A"}},
        headers={"Authorization": f"Bearer {student_token}"}
    )

    response = client.get(
        f"/api/v1/assignments/{assignment.id}/records",
        headers={"Authorization": f"Bearer {teacher_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 1


def test_update_assignment(client, db_session):
    teacher = create_test_user(db_session, "teacher1", role="teacher")
    token = create_access_token({"user_id": teacher.id, "role": teacher.role, "username": teacher.username})

    assignment = Assignment(title="原始标题", question_ids="1,2", created_by=teacher.id)
    db_session.add(assignment)
    db_session.commit()
    db_session.refresh(assignment)

    response = client.put(
        f"/api/v1/assignments/{assignment.id}",
        json={"title": "更新后的标题"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["title"] == "更新后的标题"


def test_delete_assignment(client, db_session):
    teacher = create_test_user(db_session, "teacher1", role="teacher")
    token = create_access_token({"user_id": teacher.id, "role": teacher.role, "username": teacher.username})

    assignment = Assignment(title="作业1", question_ids="1,2", created_by=teacher.id)
    db_session.add(assignment)
    db_session.commit()
    db_session.refresh(assignment)

    response = client.delete(
        f"/api/v1/assignments/{assignment.id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["data"]["message"] == "作业已删除"
