"""多租户测试 fixture

提供两个独立的 teacher 及其 token，以及班级+学生组合，
供跨租户隔离测试使用。
"""
import pytest
from app.models import User, ClassGroup, ClassMember
from app.core.security import create_access_token


@pytest.fixture
def teacher_a(db):
    u = User(username="teacher_a", password_hash=User.hash_password("abc12345"),
            role="teacher", display_name="A")
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


@pytest.fixture
def teacher_b(db):
    u = User(username="teacher_b", password_hash=User.hash_password("abc12345"),
            role="teacher", display_name="B")
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


@pytest.fixture
def teacher_a_token(teacher_a):
    return create_access_token({"user_id": teacher_a.id})


@pytest.fixture
def teacher_b_token(teacher_b):
    return create_access_token({"user_id": teacher_b.id})


@pytest.fixture
def class_b_with_student(db, teacher_b):
    cls = ClassGroup(name="B 班", created_by=teacher_b.id)
    db.add(cls)
    db.commit()
    db.refresh(cls)
    student = User(username="student_b_1", password_hash=User.hash_password("abc12345"),
                   role="student", display_name="学生 1")
    db.add(student)
    db.commit()
    db.refresh(student)
    db.add(ClassMember(class_id=cls.id, user_id=student.id))
    db.commit()
    return cls, student
