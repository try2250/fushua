from app.core.security import create_access_token
from app.models import Assignment, AssignmentRecord, ClassGroup, ClassMember, Record
from tests.conftest import create_test_question, create_test_user


def _token(user):
    return create_access_token({
        "user_id": user.id,
        "role": user.role,
        "username": user.username,
    })


def test_miniprogram_practice_record_aliases(client, db_session):
    student = create_test_user(db_session, "mini_student", role="student")
    question = create_test_question(db_session, created_by=student.id, answer="B")
    token = _token(student)

    create_response = client.post(
        "/api/v1/practice-records",
        json={"question_id": question.id, "user_answer": "A", "is_correct": False},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert create_response.status_code == 200
    assert create_response.json()["code"] == 0

    stats_response = client.get(
        "/api/v1/practice-records/today-stats",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert stats_response.status_code == 200
    assert stats_response.json()["data"]["completed"] == 1
    assert stats_response.json()["data"]["correct"] == 0

    mistakes_response = client.get(
        "/api/v1/practice-records/mistakes",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert mistakes_response.status_code == 200
    mistake = mistakes_response.json()["data"][0]
    assert mistake["id"] == create_response.json()["data"]["id"]
    assert mistake["question"]["correct_answer"] == "B"


def test_miniprogram_user_stats_and_mistakes(client, db_session):
    teacher = create_test_user(db_session, "mini_teacher", role="teacher")
    student = create_test_user(db_session, "mini_stats_student", role="student")
    question = create_test_question(db_session, created_by=teacher.id)
    db_session.add(Record(user_id=student.id, question_id=question.id, user_answer="A", is_correct=False))
    db_session.commit()

    student_response = client.get(
        "/api/v1/users/me/stats",
        headers={"Authorization": f"Bearer {_token(student)}"},
    )
    assert student_response.status_code == 200
    assert student_response.json()["data"]["total_questions"] == 1

    teacher_stats_response = client.get(
        f"/api/v1/users/{student.id}/stats",
        headers={"Authorization": f"Bearer {_token(teacher)}"},
    )
    assert teacher_stats_response.status_code == 200
    assert teacher_stats_response.json()["data"]["correct_rate"] == 0

    teacher_mistakes_response = client.get(
        f"/api/v1/users/{student.id}/mistakes",
        headers={"Authorization": f"Bearer {_token(teacher)}"},
    )
    assert teacher_mistakes_response.status_code == 200
    assert teacher_mistakes_response.json()["data"][0]["question"]["id"] == question.id


def test_miniprogram_assignment_detail_submission_and_class_member_delete(client, db_session):
    teacher = create_test_user(db_session, "mini_assign_teacher", role="teacher")
    student = create_test_user(db_session, "mini_assign_student", role="student")
    question = create_test_question(db_session, created_by=teacher.id)
    class_group = ClassGroup(name="Mini Class", created_by=teacher.id)
    db_session.add(class_group)
    db_session.commit()
    db_session.refresh(class_group)
    member = ClassMember(class_id=class_group.id, user_id=student.id)
    db_session.add(member)
    assignment = Assignment(
        title="Mini Assignment",
        description="",
        question_ids=str(question.id),
        created_by=teacher.id,
        class_id=class_group.id,
    )
    db_session.add(assignment)
    db_session.commit()
    db_session.refresh(assignment)
    db_session.refresh(member)

    detail_response = client.get(
        f"/api/v1/assignments/{assignment.id}?class_id={class_group.id}",
        headers={"Authorization": f"Bearer {_token(student)}"},
    )
    assert detail_response.status_code == 200
    detail = detail_response.json()["data"]
    assert detail["status"] == "pending"
    assert detail["questions"][0]["correct_answer"] == question.answer

    submit_response = client.post(
        f"/api/v1/assignments/{assignment.id}/submit?class_id={class_group.id}",
        json={"answers": [{"question_id": question.id, "user_answer": question.answer}]},
        headers={"Authorization": f"Bearer {_token(student)}"},
    )
    assert submit_response.status_code == 200
    assert submit_response.json()["data"]["score"] == 100

    submission_response = client.get(
        f"/api/v1/assignments/{assignment.id}/submission?class_id={class_group.id}",
        headers={"Authorization": f"Bearer {_token(student)}"},
    )
    assert submission_response.status_code == 200
    assert submission_response.json()["data"]["completed"] is True

    remove_response = client.delete(
        f"/api/v1/classes/{class_group.id}/members/{member.id}",
        headers={"Authorization": f"Bearer {_token(teacher)}"},
    )
    assert remove_response.status_code == 200
    assert remove_response.json()["data"]["message"] == "成员已移出班级"
