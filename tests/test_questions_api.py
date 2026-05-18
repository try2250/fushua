import pytest
from tests.conftest import create_test_user, create_test_question
from app.core.security import create_access_token


def test_create_question_as_teacher(client, db_session):
    teacher = create_test_user(db_session, "teacher1", role="teacher")
    token = create_access_token({"user_id": teacher.id, "role": teacher.role, "username": teacher.username})

    response = client.post(
        "/api/v1/questions",
        json={
            "subject": "数学",
            "semester": "八年级上册",
            "chapter": "代数",
            "q_type": "choice",
            "difficulty": 2,
            "content": "1+1等于几？",
            "option_a": "1",
            "option_b": "2",
            "option_c": "3",
            "option_d": "4",
            "answer": "B",
            "explanation": "1+1=2"
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 0
    assert data["data"]["content"] == "1+1等于几？"


def test_create_question_as_student_fails(client, db_session):
    student = create_test_user(db_session, "student1", role="student")
    token = create_access_token({"user_id": student.id, "role": student.role, "username": student.username})

    response = client.post(
        "/api/v1/questions",
        json={
            "subject": "数学",
            "q_type": "choice",
            "content": "测试题目",
            "answer": "A"
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 403


def test_get_questions_with_filters(client, db_session):
    teacher = create_test_user(db_session, "teacher1", role="teacher")
    token = create_access_token({"user_id": teacher.id, "role": teacher.role, "username": teacher.username})

    create_test_question(db_session, subject="数学", semester="八年级上册", created_by=teacher.id)
    create_test_question(db_session, subject="数学", semester="八年级下册", created_by=teacher.id)
    create_test_question(db_session, subject="英语", semester="八年级上册", created_by=teacher.id)

    response = client.get(
        "/api/v1/questions?subject=数学&semester=八年级上册",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 1
    assert data["data"][0]["subject"] == "数学"
    assert data["data"][0]["semester"] == "八年级上册"


def test_get_random_questions(client, db_session):
    teacher = create_test_user(db_session, "teacher1", role="teacher")
    token = create_access_token({"user_id": teacher.id, "role": teacher.role, "username": teacher.username})

    for i in range(15):
        create_test_question(db_session, subject="数学", created_by=teacher.id)

    response = client.get(
        "/api/v1/questions/random?subject=数学&count=10",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 10


def test_update_question(client, db_session):
    teacher = create_test_user(db_session, "teacher1", role="teacher")
    token = create_access_token({"user_id": teacher.id, "role": teacher.role, "username": teacher.username})

    question = create_test_question(db_session, content="原始题目", created_by=teacher.id)

    response = client.put(
        f"/api/v1/questions/{question.id}",
        json={"content": "更新后的题目"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["content"] == "更新后的题目"


def test_delete_question(client, db_session):
    teacher = create_test_user(db_session, "teacher1", role="teacher")
    token = create_access_token({"user_id": teacher.id, "role": teacher.role, "username": teacher.username})

    question = create_test_question(db_session, created_by=teacher.id)

    response = client.delete(
        f"/api/v1/questions/{question.id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["data"]["message"] == "题目已删除"
