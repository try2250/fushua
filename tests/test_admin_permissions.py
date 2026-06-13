import pytest
from app.models import ClassGroup, ClassMember
from tests.conftest import TestingSessionLocal, create_test_user, create_test_question
from app.routers.permissions import teacher_owns_student, teacher_owns_class, teacher_owns_question


def test_teacher_owns_own_resources():
    db = TestingSessionLocal()
    try:
        teacher = create_test_user(db, "teacher_resource", "teacher")
        cls = ClassGroup(name="测试班级", created_by=teacher.id)
        db.add(cls); db.commit()
        student = create_test_user(db, "student_resource", "student")
        db.add(ClassMember(class_id=cls.id, user_id=student.id))
        db.commit()
        q = create_test_question(db, created_by=teacher.id)

        assert teacher_owns_student(db, teacher.id, student.id) == True
        assert teacher_owns_class(db, teacher.id, cls.id) == True
        assert teacher_owns_question(db, teacher.id, q.id) == True
    finally:
        db.close()
