import pytest
from tests.conftest import create_test_user
from app.models import ClassGroup, ClassMember
from app.core.security import create_access_token


def test_create_class_as_teacher(client, db_session):
    teacher = create_test_user(db_session, "teacher1", role="teacher")
    token = create_access_token({"user_id": teacher.id, "role": teacher.role, "username": teacher.username})

    response = client.post(
        "/api/v1/classes",
        json={"name": "Math Class 101"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 0
    assert data["data"]["name"] == "Math Class 101"


def test_create_class_as_student_fails(client, db_session):
    # Student needs a class to resolve tenant context
    teacher = create_test_user(db_session, "for_student", role="teacher")
    cls = ClassGroup(name="A", created_by=teacher.id)
    db_session.add(cls); db_session.commit(); db_session.refresh(cls)

    student = create_test_user(db_session, "student1", role="student")
    db_session.add(ClassMember(class_id=cls.id, user_id=student.id))
    db_session.commit()

    token = create_access_token({"user_id": student.id, "role": student.role, "username": student.username})

    response = client.post(
        f"/api/v1/classes?class_id={cls.id}",
        json={"name": "Math Class 101"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 403


def test_get_classes_as_teacher(client, db_session):
    teacher = create_test_user(db_session, "teacher1", role="teacher")
    token = create_access_token({"user_id": teacher.id, "role": teacher.role, "username": teacher.username})

    class1 = ClassGroup(name="Class A", created_by=teacher.id)
    class2 = ClassGroup(name="Class B", created_by=teacher.id)
    db_session.add_all([class1, class2])
    db_session.commit()

    response = client.get(
        "/api/v1/classes",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 2


def test_join_class_as_student(client, db_session):
    teacher = create_test_user(db_session, "teacher1", role="teacher")
    student = create_test_user(db_session, "student1", role="student")
    student_token = create_access_token({"user_id": student.id, "role": student.role, "username": student.username})

    class1 = ClassGroup(name="Class A", created_by=teacher.id)
    db_session.add(class1)
    db_session.commit()
    db_session.refresh(class1)

    response = client.post(
        f"/api/v1/classes/{class1.id}/join",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    assert response.status_code == 200
    assert response.json()["data"]["message"] == "加入班级成功"


def test_get_class_detail(client, db_session):
    teacher = create_test_user(db_session, "teacher1", role="teacher")
    token = create_access_token({"user_id": teacher.id, "role": teacher.role, "username": teacher.username})

    class1 = ClassGroup(name="Class A", created_by=teacher.id)
    db_session.add(class1)
    db_session.commit()
    db_session.refresh(class1)

    response = client.get(
        f"/api/v1/classes/{class1.id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["name"] == "Class A"
    assert data["data"]["member_count"] == 0
