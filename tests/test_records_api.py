import pytest
from tests.conftest import create_test_user, create_test_question
from app.models import Record
from app.core.security import create_access_token


def test_create_record(client, db_session):
    student = create_test_user(db_session, "student1", role="student")
    token = create_access_token({"user_id": student.id, "role": student.role, "username": student.username})
    question = create_test_question(db_session, created_by=1)

    response = client.post(
        "/api/v1/records",
        json={
            "question_id": question.id,
            "user_answer": "B",
            "is_correct": True
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 0
    assert data["data"]["is_correct"] == True


def test_get_records(client, db_session):
    student = create_test_user(db_session, "student1", role="student")
    token = create_access_token({"user_id": student.id, "role": student.role, "username": student.username})
    question = create_test_question(db_session, created_by=1)

    record1 = Record(user_id=student.id, question_id=question.id, user_answer="A", is_correct=True)
    record2 = Record(user_id=student.id, question_id=question.id, user_answer="B", is_correct=False)
    db_session.add_all([record1, record2])
    db_session.commit()

    response = client.get(
        "/api/v1/records",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 2


def test_get_mistakes(client, db_session):
    student = create_test_user(db_session, "student1", role="student")
    token = create_access_token({"user_id": student.id, "role": student.role, "username": student.username})
    question = create_test_question(db_session, created_by=1)

    record1 = Record(user_id=student.id, question_id=question.id, user_answer="A", is_correct=True)
    record2 = Record(user_id=student.id, question_id=question.id, user_answer="B", is_correct=False)
    record3 = Record(user_id=student.id, question_id=question.id, user_answer="C", is_correct=False)
    db_session.add_all([record1, record2, record3])
    db_session.commit()

    response = client.get(
        "/api/v1/records/mistakes",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 2


def test_get_stats(client, db_session):
    student = create_test_user(db_session, "student1", role="student")
    token = create_access_token({"user_id": student.id, "role": student.role, "username": student.username})
    question = create_test_question(db_session, created_by=1)

    for i in range(10):
        is_correct = i < 7
        record = Record(user_id=student.id, question_id=question.id, user_answer="A", is_correct=is_correct)
        db_session.add(record)
    db_session.commit()

    response = client.get(
        "/api/v1/records/stats",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["total_count"] == 10
    assert data["data"]["correct_count"] == 7
    assert data["data"]["accuracy"] == 70.0
