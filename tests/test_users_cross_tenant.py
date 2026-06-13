"""用户跨租户隔离测试"""
from fastapi.testclient import TestClient
from app.main import app as main_app
from app.models import User, ClassGroup, ClassMember
from app.core.security import create_access_token


def _setup_student_in(db, teacher_id, class_name="班"):
    cls = ClassGroup(name=class_name, created_by=teacher_id)
    db.add(cls); db.commit(); db.refresh(cls)
    student = User(username=f"s_{teacher_id}_{class_name}", password_hash=User.hash_password("x"), role="student", display_name="Stu")
    db.add(student); db.commit(); db.refresh(student)
    db.add(ClassMember(class_id=cls.id, user_id=student.id))
    db.commit()
    return student, cls


def test_teacher_a_cannot_see_teacher_b_student_stats(db, teacher_a, teacher_b, teacher_a_token):
    student_b, cls_b = _setup_student_in(db, teacher_b.id)
    client = TestClient(main_app)
    r = client.get(f"/api/v1/users/{student_b.id}/stats", headers={"Authorization": f"Bearer {teacher_a_token}"})
    assert r.status_code == 404


def test_teacher_a_can_see_own_student_stats_with_class_id(db, teacher_a, teacher_a_token):
    student_a, cls_a = _setup_student_in(db, teacher_a.id, class_name="A 班")
    client = TestClient(main_app)
    r = client.get(f"/api/v1/users/{student_a.id}/stats?class_id={cls_a.id}", headers={"Authorization": f"Bearer {teacher_a_token}"})
    assert r.status_code == 200


def test_student_can_see_own_stats(db, teacher_a):
    student, cls = _setup_student_in(db, teacher_a.id)
    token = create_access_token({"user_id": student.id})
    client = TestClient(main_app)
    r = client.get(f"/api/v1/users/{student.id}/stats?class_id={cls.id}", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200


def test_teacher_a_cannot_see_teacher_b_student_mistakes(db, teacher_a, teacher_b, teacher_a_token):
    student_b, _ = _setup_student_in(db, teacher_b.id)
    client = TestClient(main_app)
    r = client.get(f"/api/v1/users/{student_b.id}/mistakes", headers={"Authorization": f"Bearer {teacher_a_token}"})
    assert r.status_code == 404
